#!/usr/bin/env python3
"""
MithuLoopMaker — যেকোনো ভিডিওকে অসীম লুপে বদলে দাও 🔁

বৈশিষ্ট্য:
  • Boomerang লুপ: সামনে + উল্টো = 100% seamless (কোনো ঝাঁকুনি নেই)
  • --repeat দিয়ে এক ফাইলে একাধিক লুপ (watch time বাড়ায়)
  • অডিও-ও উল্টে যায়, তাই শব্দেও লুপ মসৃণ

ব্যবহার:
  python3 make_loop.py video.mp4                 # সাধারণ লুপ (২x দৈর্ঘ্য)
  python3 make_loop.py video.mp4 --repeat 5      # ৫ বার লুপ = ১০x দৈর্ঘ্য
  python3 make_loop.py video.mp4 --out my_loop.mp4
"""
import argparse
import os
import re
import subprocess
import sys

FFMPEG = os.path.expanduser("~/.local/bin/ffmpeg")


def run(cmd, quiet=True):
    args = cmd[:2] + (["-hide_banner", "-loglevel", "error"] if quiet else []) + cmd[2:]
    subprocess.run(args, check=True)


def probe(path):
    """ভিডিওর দৈর্ঘ্য আর অডিও আছে কিনা বের করা।

    RuntimeError ছাড়ি (SystemExit নয়) — যাতে সার্ভারগুলোর
    `except Exception` হ্যান্ডলার ধরতে পারে আর ব্রাউজারে সঠিক
    এরর দেখায়।
    """
    p = subprocess.run([FFMPEG, "-hide_banner", "-i", path],
                       capture_output=True, text=True)
    m = re.search(r"Duration: (\d+):(\d+):(\d+(?:\.\d+)?)", p.stderr)
    if not m:
        raise RuntimeError(f"'{path}' পড়া যাচ্ছে না — ফাইলটা ঠিক আছে?")
    h, mi, s = m.groups()
    dur = int(h) * 3600 + int(mi) * 60 + float(s)
    has_audio = "Audio:" in p.stderr
    return dur, has_audio


def make_boomerang(src, out, has_audio):
    """সামনে + উল্টো (reverse) = math-নিখুঁত seamless লুপ।"""
    if has_audio:
        fc = (
            "[0:v]split[v1][v2];"
            "[v2]reverse[vr];"
            "[v1][vr]concat=n=2:v=1:a=0[v];"
            "[0:a]asplit[a1][a2];"
            "[a2]areverse[ar];"
            "[a1][ar]concat=n=2:v=0:a=1[a]"
        )
        maps = ["-map", "[v]", "-map", "[a]", "-c:a", "aac", "-b:a", "192k"]
    else:
        fc = "[0:v]split[v1][v2];[v2]reverse[vr];[v1][vr]concat=n=2:v=1:a=0[v]"
        maps = ["-map", "[v]", "-an"]

    run([FFMPEG, "-y", "-i", src, "-filter_complex", fc, *maps,
         "-r", "30",
         "-c:v", "libx264", "-preset", "fast", "-crf", "18",
         "-pix_fmt", "yuv420p", "-movflags", "+faststart", out])


def repeat_file(src, out, times):
    """একই লুপ ফাইল N বার জোড়া লাগানো (encode ছাড়াই, দ্রুত)।"""
    run([FFMPEG, "-y", "-stream_loop", str(times - 1), "-i", src,
         "-c", "copy", "-movflags", "+faststart", out])


def main():
    ap = argparse.ArgumentParser(description="ভিডিওকে seamless লুপে বদলাও")
    ap.add_argument("input", help="ইনপুট ভিডিও (mp4/mov)")
    ap.add_argument("--repeat", type=int, default=1,
                    help="কতবার লুপ করবে (ডিফল্ট ১ = ২x দৈর্ঘ্য)")
    ap.add_argument("--out", default=None, help="আউটপুট ফাইল")
    args = ap.parse_args()

    if not os.path.exists(args.input):
        raise SystemExit(f"❌ ফাইল নেই: {args.input}")

    base = os.path.splitext(os.path.basename(args.input))[0]
    out = args.out or f"{base}_loop.mp4"
    if not out.endswith(".mp4"):
        out += ".mp4"

    try:
        dur, has_audio = probe(args.input)
    except RuntimeError as e:
        raise SystemExit(f"❌ {e}")
    print(f"""
🔁 MithuLoopMaker
━━━━━━━━━━━━━━━━━━━━━
🎬 ইনপুট     : {os.path.basename(args.input)}
⏱️  দৈর্ঘ্য    : {dur:.2f}s  (অডিও: {'✅' if has_audio else '❌ নেই'})
🔂 লুপ       : {args.repeat} বার
📐 ফাইনাল    : ~{dur * 2 * args.repeat:.1f}s
━━━━━━━━━━━━━━━━━━━━━""")

    if args.repeat == 1:
        print("🔄 boomerang লুপ তৈরি হচ্ছে (সামনে + উল্টো)...")
        make_boomerang(args.input, out, has_audio)
    else:
        import tempfile
        with tempfile.TemporaryDirectory(prefix="mithuloop_") as tmp:
            one = os.path.join(tmp, "one.mp4")
            print("🔄 boomerang লুপ তৈরি হচ্ছে...")
            make_boomerang(args.input, one, has_audio)
            print(f"📚 {args.repeat} বার জোড়া লাগানো হচ্ছে...")
            repeat_file(one, out, args.repeat)

    size = os.path.getsize(out) / (1024 * 1024)
    print(f"""
✅ লুপ রেডি!
   📁 {os.path.abspath(out)}
   💾 {size:.1f} MB
   🔁 অসীম লুপ — কোনো ঝাঁকুনি নেই, কারণ শেষ ফ্রেম = প্রথম ফ্রেম
""")


if __name__ == "__main__":
    main()
