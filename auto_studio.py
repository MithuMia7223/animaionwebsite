#!/usr/bin/env python3
"""
MithuAuto — ফোল্ডারে ছবি ফেললেই অটো-ভিডিও 🎬

ব্যবহার:
  assets/auto_in/ ফোল্ডারে একটা নতুন ফোল্ডার বানিয়ে তাতে ছবি ফেলো
  (যেমন: assets/auto_in/rajur_din/01.png, 02.png ...) — বাকিটা অটোমেটিক:

    ১. ভিডিও বানায় (Ken Burns + ফ্যান্সি ট্রানজিশন + মিউজিক)
    ২. assets/output/auto_<নাম>.mp4 নামে জমা করে
    ৩. কাজ শেষে ফোল্ডারটা assets/auto_in/done/ এ সরিয়ে রাখে

চালাও:
  python3 auto_studio.py            ← চালু থাকে, প্রতি ৩ সেকেন্ডে নতুন কাজ খোঁজে
  python3 auto_studio.py --once     ← একবার দেখে বেরিয়ে যায় (cron-এর জন্য)
  python3 auto_studio.py --horizontal --seconds 4   ← ল্যান্ডস্কেপ + দৈর্ঘ্য
"""
import argparse
import os
import shutil
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.abspath(__file__))
IN = os.path.join(ROOT, "assets", "auto_in")
DONE = os.path.join(IN, "done")
OUT = os.path.join(ROOT, "assets", "output")
MUSIC = os.path.join(ROOT, "assets", "music", "demo_pad.m4a")
IMG_EXT = (".jpg", ".jpeg", ".png", ".webp", ".bmp")


def jobs():
    """auto_in/-এ ছবি-আছে-এমন ফোল্ডারগুলোর তালিকা"""
    if not os.path.isdir(IN):
        return []
    out = []
    for d in sorted(os.listdir(IN)):
        full = os.path.join(IN, d)
        if d == "done" or not os.path.isdir(full):
            continue
        if any(f.lower().endswith(IMG_EXT) for f in os.listdir(full)):
            out.append(full)
    return out


def run_job(folder, horizontal, seconds):
    name = os.path.basename(folder)
    os.makedirs(OUT, exist_ok=True)
    out_path = os.path.join(OUT, f"auto_{name}.mp4")

    cmd = [sys.executable, os.path.join(ROOT, "make_video.py"), folder,
           "--fancy", "--out", out_path]
    cmd += [] if horizontal else ["--vertical"]
    cmd += ["--seconds", str(seconds)]
    if os.path.exists(MUSIC):
        cmd += ["--music", MUSIC]

    print(f"🎬 অটো-রেন্ডার শুরু: {name}")
    r = subprocess.run(cmd, cwd=ROOT)
    ok = (r.returncode == 0 and os.path.exists(out_path))

    # ফোল্ডাটা done/-এ সরাই (একই নাম থাকলে সময় জুড়ে দিই)
    os.makedirs(DONE, exist_ok=True)
    dest = os.path.join(DONE, name)
    if os.path.exists(dest):
        dest += "_" + time.strftime("%H%M%S")
    shutil.move(folder, dest)

    if ok:
        mb = os.path.getsize(out_path) / (1024 * 1024)
        print(f"✅ ভিডিও রেডি: {out_path}  ({mb:.1f} MB)")
    else:
        print(f"❌ রেন্ডার এরর — ফোল্ডারটা done/-এ আছে, পরে আবার চেষ্টা করা যাবে")
    return ok


def main():
    ap = argparse.ArgumentParser(description="ফোল্ডার-ওয়াচার অটো-ভিডিও মেকার")
    ap.add_argument("--once", action="store_true", help="একবার স্ক্যান করে বেরিয়ে যাও")
    ap.add_argument("--horizontal", action="store_true", help="16:9 (না দিলে 9:16 Reels)")
    ap.add_argument("--seconds", type=float, default=4.0, help="প্রতি ছবি কত সেকেন্ড (ডিফল্ট ৪)")
    ap.add_argument("--every", type=float, default=3.0, help="কত সেকেন্ড পরপর দেখবে")
    args = ap.parse_args()

    os.makedirs(IN, exist_ok=True)
    print(f"""
🤖 MithuAuto চালু — ফোল্ডার: {IN}
   ছবি ফেললেই অটো ভিডিও হবে। বন্ধ করতে: Ctrl + C
""")

    while True:
        try:
            for folder in jobs():
                run_job(folder, args.horizontal, args.seconds)
        except KeyboardInterrupt:
            print("\n👋 বন্ধ করা হলো।")
            return
        if args.once:
            return
        time.sleep(max(1.0, args.every))


if __name__ == "__main__":
    main()
