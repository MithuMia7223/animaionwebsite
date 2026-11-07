#!/usr/bin/env python3
"""
MithuStudio — তোমার নিজের কপিরাইট-ফ্রি ভিডিও স্টুডিও 🎬
সবকিছু তোমার কম্পিউটারেই তৈরি হয় — কোনো ইন্টারনেট, সাবস্ক্রিপশন বা কপিরাইট নেই।

চালাও:  python3 server.py
তারপর:   http://127.0.0.1:8765
"""
import base64
import json
import os
import re
import shutil
import sys
import tempfile
import uuid
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

ROOT = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(ROOT)
sys.path.insert(0, PROJECT)

import make_video as mv      # noqa: E402
import make_loop as ml       # noqa: E402

WEB = os.path.join(ROOT, "web")
OUT = os.path.join(ROOT, "output")
PORT = 8765

os.makedirs(OUT, exist_ok=True)


# ---------------------------------------------------------------- music
MUSIC_PRESETS = {
    # ধীর, শান্ত প্যাড — বেডটাইম/ক্যালাম ভিডিওর জন্য
    "calm": (
        "(0.75+0.25*sin(2*PI*0.08*t))*("
        "0.060*sin(2*PI*220.00*t)+"
        "0.050*sin(2*PI*277.18*t)+"
        "0.040*sin(2*PI*329.63*t)+"
        "0.030*sin(2*PI*440.00*t))"
    ),
    # উজ্জ্বল, আনন্দময় — কিডস/প্রোডাক্ট ভিডিওর জন্য
    "bright": (
        "(0.70+0.30*sin(2*PI*0.35*t))*("
        "0.055*sin(2*PI*261.63*t)+"
        "0.045*sin(2*PI*329.63*t)+"
        "0.040*sin(2*PI*392.00*t)+"
        "0.022*sin(2*PI*523.25*t))"
    ),
}


def make_music(kind: str, dur: float, path: str) -> bool:
    """রয়্যালটি-ফ্রি ব্যাকগ্রাউন্ড মিউজিক তৈরি (সম্পূর্ণ সিন্থেসাইজড)।"""
    expr = MUSIC_PRESETS.get(kind)
    if not expr:
        return False
    dur = max(1.0, min(dur + 2.0, 600.0))
    mv.run([mv.FFMPEG, "-y", "-f", "lavfi",
            "-i", f"aevalsrc={expr}:s=44100:d={dur:.2f}",
            "-c:a", "aac", "-b:a", "192k", path])
    return True


# ---------------------------------------------------------------- pipeline
def build(payload: dict) -> dict:
    images = payload.get("images") or []
    if not images:
        return {"ok": False, "error": "কোনো ছবি পাওয়া যায়নি — অন্তত ১টা ছবি দাও।"}

    seconds = float(payload.get("seconds", 5))
    seconds = max(1.5, min(15.0, seconds))
    vertical = bool(payload.get("vertical", True))
    title = (payload.get("title") or "").strip() or None
    fancy = bool(payload.get("fancy", True))
    music_kind = payload.get("music", "calm")
    do_loop = bool(payload.get("loop", True))
    repeat = int(payload.get("repeat", 3))
    repeat = max(1, min(20, repeat))

    w, h = (1080, 1920) if vertical else (1920, 1080)
    fade = min(0.6, seconds * 0.3)

    job = uuid.uuid4().hex[:10]
    work = tempfile.mkdtemp(prefix=f"studio_{job}_")
    try:
        # ---- ছবি সেভ করা
        img_paths = []
        for i, item in enumerate(images):
            data = item.get("data", "")
            if "," not in data:
                continue
            b64 = data.split(",", 1)[1]
            raw = base64.b64decode(b64)
            ext = os.path.splitext(item.get("name", "img.png"))[1] or ".png"
            p = os.path.join(work, f"img_{i:03d}{ext}")
            with open(p, "wb") as f:
                f.write(raw)
            img_paths.append(p)

        if not img_paths:
            return {"ok": False, "error": "ছবি পড়া যায়নি।"}

        # ---- সেগমেন্ট
        segs = []
        for i, p in enumerate(img_paths):
            seg = os.path.join(work, f"seg_{i:03d}.mp4")
            mv.make_segment(p, w, h, seconds, seg)
            segs.append(seg)

        # ---- জোড়া
        combined = os.path.join(work, "combined.mp4")
        total = mv.concat_xfade(segs, seconds, fade, fancy, combined)

        # ---- টাইটেল + fade (লুপ হলে fade বন্ধ, নাহলে মাঝখানে কালো হয়)
        clean = os.path.join(work, "clean.mp4")
        mv.title_overlay_and_finish(combined, total, title, None, w, h, clean,
                                    fades=not do_loop)

        # ---- মিউজিক
        current = clean
        if music_kind in MUSIC_PRESETS:
            music = os.path.join(work, "music.m4a")
            make_music(music_kind, total, music)
            with_music = os.path.join(work, "with_music.mp4")
            mv.mux_with_music(current, music, total, with_music,
                              fades=not do_loop)
            current = with_music

        # ---- লুপ (boomerang = seamless)
        if do_loop:
            looped = os.path.join(work, "looped.mp4")
            _, has_audio = ml.probe(current)
            ml.make_boomerang(current, looped, has_audio)
            if repeat > 1:
                final = os.path.join(work, "final.mp4")
                ml.repeat_file(looped, final, repeat)
                current = final
            else:
                current = looped

        out_name = f"video_{job}.mp4"
        out_path = os.path.join(OUT, out_name)
        shutil.copy(current, out_path)

        size = os.path.getsize(out_path) / (1024 * 1024)
        return {
            "ok": True,
            "url": f"/output/{out_name}",
            "name": out_name,
            "size_mb": round(size, 1),
            "seconds": round(total, 1),
            "loop_seconds": round(total * (2 if do_loop else 1) * repeat, 1),
        }
    finally:
        shutil.rmtree(work, ignore_errors=True)


# ---------------------------------------------------------------- http
class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=WEB, **kw)

    def log_message(self, *args):
        pass

    def _serve_video(self, full):
        """Range সাপোর্ট সহ ভিডিও পাঠানো (সিক করে দেখার জন্য)।"""
        size = os.path.getsize(full)
        start, end = 0, size - 1
        rng = self.headers.get("Range")
        partial = False

        if rng and rng.startswith("bytes="):
            try:
                spec = rng.split("=", 1)[1].split(",")[0]
                s, e = spec.split("-", 1)
                if s.strip():
                    start = int(s)
                if e.strip():
                    end = min(int(e), size - 1)
                partial = True
            except Exception:  # noqa: BLE001
                start, end = 0, size - 1
                partial = False

        if start > end or start >= size:
            self.send_response(416)
            self.send_header("Content-Range", f"bytes */{size}")
            self.send_header("Content-Length", "0")
            self.end_headers()
            return

        length = end - start + 1
        self.send_response(206 if partial else 200)
        self.send_header("Content-Type", "video/mp4")
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Length", str(length))
        if partial:
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.end_headers()

        with open(full, "rb") as f:
            f.seek(start)
            left = length
            while left > 0:
                chunk = f.read(min(262144, left))
                if not chunk:
                    break
                self.wfile.write(chunk)
                left -= len(chunk)

    def do_GET(self):
        path = urlparse(self.path).path

        if path.startswith("/output/"):
            name = os.path.basename(path)
            full = os.path.join(OUT, name)
            if os.path.exists(full):
                self._serve_video(full)
                return
            self.send_error(404)
            return

        if path.startswith("/files/"):
            from urllib.parse import unquote
            name = os.path.basename(unquote(path))
            full = os.path.join(OUT, name)
            if os.path.exists(full):
                self.send_response(200)
                self.send_header("Content-Type", "application/octet-stream")
                self.send_header("Content-Disposition",
                                 f'attachment; filename="{name}"')
                self.send_header("Content-Length", str(os.path.getsize(full)))
                self.end_headers()
                with open(full, "rb") as f:
                    shutil.copyfileobj(f, self.wfile)
                return
            self.send_error(404)
            return

        if path == "/":
            self.path = "/index.html"
        return super().do_GET()

    def do_POST(self):
        if urlparse(self.path).path != "/api/generate":
            self.send_error(404)
            return
        try:
            length = int(self.headers.get("Content-Length", 0))
            payload = json.loads(self.rfile.read(length) or b"{}")
            result = build(payload)
        except Exception as e:  # noqa: BLE001
            result = {"ok": False, "error": f"{type(e).__name__}: {e}"}

        body = json.dumps(result, ensure_ascii=False).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else PORT
    srv = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"""
🎬 MithuStudio চালু হয়েছে!

   👉 ব্রাউজারে খোলো:  http://127.0.0.1:{port}

   সব ভিডিও ও মিউজিক তোমার কম্পিউটারেই তৈরি হয় — ১০০% কপিরাইট-ফ্রি।
   বন্ধ করতে: Ctrl + C
""")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 বন্ধ করা হলো।")


if __name__ == "__main__":
    main()
