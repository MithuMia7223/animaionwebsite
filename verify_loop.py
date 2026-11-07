#!/usr/bin/env python3
"""
MithuLoopVerifier — ভিডিওর লুপ সত্যিই seamless কিনা মেপে বলে দেয় 🔬

কীভাবে কাজ করে:
  ১. প্রথম ফ্রেম আর শেষ ফ্রেম আলাদা করে বের করে
  ২. দুটোর মধ্যে SSIM (structural similarity) মাপে
  ৩. স্কোর অনুযায়ী রায় দেয়

ব্যবহার:
  python3 verify_loop.py video.mp4
"""
import argparse
import os
import re
import subprocess
import sys
import tempfile

FFMPEG = os.path.expanduser("~/.local/bin/ffmpeg")


def probe(path):
    p = subprocess.run([FFMPEG, "-hide_banner", "-i", path],
                       capture_output=True, text=True)
    if "Duration:" not in p.stderr:
        raise SystemExit(f"❌ '{path}' ভিডিও হিসেবে পড়া যাচ্ছে না")
    dur = re.search(r"Duration: (\d+):(\d+):(\d+(?:\.\d+)?)", p.stderr)
    secs = int(dur.group(1)) * 3600 + int(dur.group(2)) * 60 + float(dur.group(3))
    size = re.search(r"Video:.*?, (\d{2,5})x(\d{2,5})", p.stderr)
    if not size:
        raise SystemExit("❌ ভিডিওর সাইজ পাওয়া গেল না")
    return secs, int(size.group(1)), int(size.group(2))


def grab_frame(src, out, first=True):
    if first:
        cmd = [FFMPEG, "-y", "-i", src, "-vf", "select=eq(n\\,0)",
               "-frames:v", "1", out]
    else:
        cmd = [FFMPEG, "-y", "-sseof", "-0.15", "-i", src,
               "-update", "1", "-frames:v", "1", out]
    subprocess.run(cmd[:2] + ["-hide_banner", "-loglevel", "error"] + cmd[2:],
                   check=True)


def ssim(a, b, w, h):
    """দুই ফ্রেমের SSIM মাপা (০ = সম্পূর্ণ আলাদা, ১ = হুবহু এক)।"""
    fc = (f"[0:v]scale={w}:{h},format=yuv420p[x];"
          f"[1:v]scale={w}:{h},format=yuv420p[y];[x][y]ssim")
    p = subprocess.run(
        [FFMPEG, "-hide_banner", "-i", a, "-i", b, "-lavfi", fc,
         "-f", "null", "-"],
        capture_output=True, text=True)
    m = re.search(r"All:([0-9.]+)", p.stderr)
    if not m:
        raise SystemExit("❌ SSIM মাপা গেল না:\n" + p.stderr[-400:])
    return float(m.group(1))


def main():
    ap = argparse.ArgumentParser(description="লুপ seamless কিনা যাচাই করো")
    ap.add_argument("input", help="ভিডিও ফাইল")
    ap.add_argument("--min", type=float, default=0.97,
                    help="পাস মার্ক (ডিফল্ট ০.৯৭)")
    args = ap.parse_args()

    if not os.path.exists(args.input):
        raise SystemExit(f"❌ ফাইল নেই: {args.input}")

    dur, w, h = probe(args.input)
    print(f"""
🔬 MithuLoopVerifier
━━━━━━━━━━━━━━━━━━━━━━━━
🎬 ফাইল   : {os.path.basename(args.input)}
⏱️  দৈর্ঘ্য : {dur:.2f}s
📐 সাইজ   : {w}x{h}
━━━━━━━━━━━━━━━━━━━━━━━━""")

    with tempfile.TemporaryDirectory(prefix="loopcheck_") as tmp:
        f1 = os.path.join(tmp, "first.png")
        f2 = os.path.join(tmp, "last.png")
        grab_frame(args.input, f1, first=True)
        grab_frame(args.input, f2, first=False)

        score = ssim(f1, f2, w, h)

        # সামান্য তথ্য: ফ্রেম দুটোর সাইজ
        s1 = os.path.getsize(f1)
        s2 = os.path.getsize(f2)

    verdict = "🟢 নিখুঁত লুপ — কোনো ঝাঁকুনি নেই!" if score >= 0.995 else \
              "🟢 চমৎকার লুপ" if score >= 0.985 else \
              "🟡 গ্রহণযোগ্য, তবে উন্নতি করা যায়" if score >= args.min else \
              "🔴 লুপে ঝাঁকুনি আছে — ঠিক করতে হবে"

    bar_len = 30
    filled = int(round(score * bar_len))
    bar = "█" * filled + "░" * (bar_len - filled)

    print(f"""
📊 SSIM স্কোর : {score:.4f}
   [{bar}]  {score*100:.1f}%

{verdict}

💡 {'প্রথম আর শেষ ফ্রেম প্রায় একই — লুপ মসৃণ হবে।' if score >= args.min else
     'পরামর্শ: শেষ ফ্রেমটা প্রথম ফ্রেমের মতো করুন, নয়তো চালান:'
     + chr(10) + '   python3 make_loop.py ' + os.path.basename(args.input) + '   (boomerang লুপ)'}
""")


if __name__ == "__main__":
    main()
