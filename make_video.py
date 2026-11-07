#!/usr/bin/env python3
"""
MithuVideoMaker - Automatic slideshow video maker (local, unlimited, free)
Owner: Mithun
Requir: শুধু ffmpeg (= ~/.local/bin/ffmpeg) এবং Python 3

ব্যবহার (এক লাইনে):
  python3 make_video.py assets/images --title "My Video" --vertical

  python3 make_video.py assets/images --music assets/music/pad.mp3 --fancy

প্রথম ছবির নাম ক্রমানুসারে (01, 02, 03...) সর্ট হয়।
"""
import argparse
import glob
import os
import subprocess
import sys
import tempfile
import shutil
from pathlib import Path

FFMPEG = os.path.expanduser("~/.local/bin/ffmpeg")
FPS = 30

IMAGE_EXT = ("*.jpg", "*.jpeg", "*.png", "*.webp", "*.bmp")

TRANSITIONS = None

def collect_images(folder: Path):
    """Folder-এর সব ছবি নাম অনুযায়ী সর্ট করে লিস্ট করা।"""
    files = []
    for ext in IMAGE_EXT:
        files.extend(glob.glob(str(folder / ext)))
        files.extend(glob.glob(str(folder / ext.upper())))
    files = sorted(set(files))
    if not files:
        raise SystemExit(f"❌ '{folder}' folder-এ কোনো ছবি পাওয়া যায়নি। (jpg/png/webp দিন)")
    return files


def esc_drawtext(s: str) -> str:
    """drawtext-এর জন্য নিরাপদ টেক্সট escaping।"""
    return (
        s.replace("\\", "\\\\")
        .replace(":", "\\:")
        .replace("'", "\\'")
        .replace(",", "\\,")
        .replace("[", "\\[")
        .replace("]", "\\]")
        .replace("%", "\\%")
    )


def find_font(user_font: str | None) -> str | None:
    """ফন্ট ফাইল বের করার চেষ্টা: প্রথমে ইউজারের, তারপর macOS ডিফল্ট।"""
    candidates = []
    if user_font:
        candidates.append(user_font)
    candidates += [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/Supplemental/Tahoma.ttf",
    ]
    for c in candidates:
        if c and os.path.exists(c):
            return c
    return None


def run(cmd):
    quiet = ["-hide_banner", "-loglevel", "error"]
    printable = " ".join(str(c) for c in cmd)
    if len(printable) > 140:
        printable = printable[:140] + " ..."
    print("  →", printable)
    subprocess.run(cmd[:2] + quiet + cmd[2:], check=True)


def make_segment(img: str, w: int, h: int, dur: float, out: str):
    """একটি ছবি থেকে Ken-Burns (ধীরে জুম) ভিডিও সেগমেন্ট বানানো।"""
    d = int(dur * FPS + 0.5)  # সঠিক ফ্রেম সংখ্যা (ফ্রেম=দৈর্ঘ্য*ফ্রেমরেট)
    # সেকেন্ড-প্রতি জুম-গতি আগের মতোই রাখি (0.0225 * 5/dur প্রতি সেকেন্ড) —
    # ফ্রেমরেট বদলালেও জুমের গতি বদলাবে না
    zoom_rate = 0.0225 * (5.0 / dur) / FPS
    vf = (
        f"scale={w*2}:-2,"
        f"zoompan=z='min(zoom+{zoom_rate:.5f},1.35)':"
        f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
        f"d={d}:s={w}x{h}:fps={FPS},"
        "format=yuv420p"
    )
    run([
        FFMPEG, "-y", "-loop", "1", "-i", img,
        "-vf", vf, "-t", str(dur), "-r", str(FPS),
        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        "-an", out,
    ])


def concat_xfade(segments, dur: float, fade: float, fancy: bool, out: str):
    """সেগমেন্টগুলোকে crossfade দিয়ে জোড়া লাগানো।"""
    n = len(segments)
    if n == 1:
        shutil.copy(segments[0], out)
        return dur

    zoom_trans = [
        "fade", "smoothleft", "circleopen", "slideright",
        "smoothup", "distance", "squeezeh", "circlecrop",
    ]
    parts = []
    prev_label = "[0:v]"
    seg_frames = int(dur * FPS + 0.5)
    d_actual = seg_frames / FPS
    total = n * d_actual - (n - 1) * fade
    for i in range(n - 1):
        tr = zoom_trans[i % len(zoom_trans)] if fancy else "fade"
        outlabel = f"[v{i+1}]"
        # offset = এখন পর্যন্ত জমে থাকা দৈর্ঘ্য − fade; i যেহেতু 0 থেকে শুরু,
        # তাই i-তম xfade-এর অফসেট = (i+1)*(D−fade)
        offset = round((i + 1) * (d_actual - fade), 3)
        parts.append(
            f"{prev_label}[{i+1}:v]xfade=transition={tr}:duration={fade}:offset={offset}{outlabel}"
        )
        prev_label = outlabel

    cmd = [FFMPEG, "-y"]
    for seg in segments:
        cmd += ["-i", seg]
    cmd += ["-filter_complex", ";".join(parts), "-map", prev_label,
            "-c:v", "libx264", "-preset", "fast", "-crf", "20", "-an", out]
    run(cmd)
    return total


def title_overlay_and_finish(video: str, total: float, title: str | None,
                             font: str | None, w: int, h: int, out: str,
                             fades: bool = True):
    """শেষ ধাপ: fade in/out + অপশনাল টাইটেল + আউটপুট ফাইনালাইজ।

    fades=False দিলে কোনো fade বসে না — লুপ ভিডিওর জন্য দরকার,
    কারণ fade থাকলে boomerang-এর মাঝখানে পর্দা কালো হয়ে যায়।
    """
    fade_out_start = max(0.0, total - 1.2)
    chain = []

    if title:
        fontfile = find_font(font)
        if not fontfile:
            print("  ⚠️ ফন্ট পাওয়া যায়নি — টাইটেল বাদ")
            title = None
        else:
            fs = int(h / 14)
            t = esc_drawtext(title)
            alpha = (
                "if(lt(t,0.6),0,if(lt(t,1.2),(t-0.6)/0.6,"
                "if(lt(t,3.8),1,if(lt(t,4.4),(4.4-t)/0.6,0))))"
            )
            chain.append(
                f"drawtext=fontfile='{fontfile}':text='{t}':"
                f"fontsize={fs}:fontcolor=white:borderw=3:bordercolor=black:"
                f"x=(w-text_w)/2:y=h*0.72:alpha='{alpha}'"
            )

    if fades:
        chain.append("fade=t=in:st=0:d=0.9")
        chain.append(f"fade=t=out:st={fade_out_start:.2f}:d=1.2")
    chain.append("format=yuv420p")

    cmd = [FFMPEG, "-y", "-i", video,
           "-vf", ",".join(chain),
           "-c:v", "libx264", "-preset", "fast", "-crf", "20", "-an", out]
    run(cmd)


def mux_with_music(video: str, music: str, total: float, out: str,
                   fades: bool = True):
    """ভিডিওর সাথে ব্যাকগ্রাউন্ড মিউজিক যোগ (অটো ট্রিম + fade out)।

    fades=False দিলে অডিওতে কোনো fade বসে না — লুপ ভিডিওর জন্য।
    """
    if fades:
        a = (
            f"atrim=0:{total:.2f},afade=t=in:st=0:d=1,"
            f"afade=t=out:st={max(0,total-2):.2f}:d=2,volume=0.9[a]"
        )
    else:
        a = f"atrim=0:{total:.2f},volume=0.9[a]"
    cmd = [FFMPEG, "-y", "-i", video, "-i", music,
           "-filter_complex", a,
           "-map", "0:v", "-map", "[a]",
           "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
           "-shortest", out]
    run(cmd)


def main():
    p = argparse.ArgumentParser(
        description="MithuVideoMaker — ছবির ফোল্ডার থেকে অটোমেটিক ভিডিও বানানো")
    p.add_argument("images", help="ছবির ফোল্ডার (যেমন: assets/images)")
    p.add_argument("--music", default=None, help="ব্যাকগ্রাউন্ড মিউজিক (mp3/wav/m4a)")
    p.add_argument("--title", default=None, help="প্রথম দৃশ্যে দেখানোর টাইটেল")
    p.add_argument("--font", default=None, help="কাস্টম ফন্ট ফাইল (ttf)")
    p.add_argument("--vertical", action="store_true", help="Reels/Shorts মোড (1080x1920)")
    p.add_argument("--fancy", action="store_true", help="বিভিন্ন ধরনের ট্রানজিশন")
    p.add_argument("--seconds", type=float, default=5.0, help="প্রতি ছবি কত সেকেন্ড (ডিফল্ট 5)")
    p.add_argument("--out", default=None, help="আউটপুট ফাইলের নাম")
    args = p.parse_args()

    folder = Path(args.images).expanduser().resolve()
    images = collect_images(folder)
    w, h = (1080, 1920) if args.vertical else (1920, 1080)
    fade = min(0.6, args.seconds * 0.3)

    out_dir = folder.parent / "output"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_name = args.out or "my_video.mp4"
    if not out_name.endswith(".mp4"):
        out_name += ".mp4"
    out_path = out_dir / out_name

    total_expected = len(images) * args.seconds - (len(images) - 1) * fade

    print(f"""
🎬 MithuVideoMaker
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📸 ছবি  : {len(images)} টি
📐 সাইজ : {w}x{h} {'(Reels/Shorts)' if args.vertical else '(YouTube 16:9)'}
⏱️  মোট দৈর্ঘ্য : {total_expected:.1f} সেকেন্ড
🎵 মিউজিক : {'✅ ' + args.music if args.music else '—'}
✍️  টাইটেল : {'✅ ' + args.title if args.title else '—'}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")

    with tempfile.TemporaryDirectory(prefix="mithu_") as tmp:
        segments = []
        for i, img in enumerate(images):
            seg = os.path.join(tmp, f"seg_{i:03d}.mp4")
            print(f"📷 [{i+1}/{len(images)}] {Path(img).name}")
            make_segment(img, w, h, args.seconds, seg)
            segments.append(seg)

        print("🔗 ক্রসফেড দিয়ে জোড়া লাগানো হচ্ছে...")
        combined = os.path.join(tmp, "combined.mp4")
        total = concat_xfade(segments, args.seconds, fade, args.fancy, combined)

        print("✨ ফাইনাল টাচ (fade + টাইটেল)...")
        clean = os.path.join(tmp, "clean.mp4")
        title_overlay_and_finish(combined, total, args.title, args.font, w, h, clean)

        if args.music:
            print("🎵 মিউজিক যোগ করা হচ্ছে...")
            mux_with_music(clean, args.music, total, str(out_path))
        else:
            shutil.copy(clean, out_path)

    size = out_path.stat().st_size / (1024 * 1024)
    print(f"""
✅ তৈরি হয়ে গেছে! তোমার ভিডিও:
   📁 {out_path}
   💾 {size:.1f} MB   ⏱️ {total:.1f} সেকেন্ড

আর ভিডিও চাইলে নতুন ছবি ফেলে আবার চালাও — আনলিমিটেড! 🎉
""")


if __name__ == "__main__":
    main()
