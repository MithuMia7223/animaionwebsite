#!/usr/bin/env python3
"""
MithuAnimator — ব্রাউজারে অ্যানিমেশন বানিয়ে MP4 নামাও 🎬

কীভাবে চালাবে:
    python3 animator/server.py
তারপর ব্রাউজারে: http://127.0.0.1:8766

সব কিছু লোকাল — কোনো API, সাবস্ক্রিপশন বা ওয়াটারমার্ক নেই।
ব্রাউজার অ্যানিমেশনটা WebM/MP4-এ রেকর্ড করে, এই সার্ভার ffmpeg দিয়ে
সেটাকে পরিষ্কার H.264 MP4 বানায় (+ ঐচ্ছিক মিউজিক + সিমলেস লুপ)।
"""
import json
import os
import shutil
import sys
import tempfile
import uuid
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, unquote, urlparse

ROOT = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(ROOT)
sys.path.insert(0, PROJECT)

import make_video as mv      # noqa: E402
import make_loop as ml       # noqa: E402

WEB = os.path.join(ROOT, "web")
OUT = os.path.join(ROOT, "output")
PORT = 8766

os.makedirs(OUT, exist_ok=True)


# ------------------------------------------------------------------ মিউজিক
MUSIC_PRESETS = {
    "calm": (
        "(0.75+0.25*sin(2*PI*0.08*t))*("
        "0.060*sin(2*PI*220.00*t)+"
        "0.050*sin(2*PI*277.18*t)+"
        "0.040*sin(2*PI*329.63*t)+"
        "0.030*sin(2*PI*440.00*t))"
    ),
    "bright": (
        "(0.70+0.30*sin(2*PI*0.35*t))*("
        "0.055*sin(2*PI*261.63*t)+"
        "0.045*sin(2*PI*329.63*t)+"
        "0.040*sin(2*PI*392.00*t)+"
        "0.022*sin(2*PI*523.25*t))"
    ),
    "playful": (
        "(0.60+0.40*sin(2*PI*0.6*t))*("
        "0.050*sin(2*PI*392.00*t)+"
        "0.038*sin(2*PI*493.88*t)+"
        "0.032*sin(2*PI*587.33*t)+"
        "0.020*sin(2*PI*783.99*t))"
    ),
}


def make_music(kind: str, dur: float, path: str) -> bool:
    """রয়্যালটি-ফ্রি ব্যাকগ্রাউন্ড মিউজিক (সম্পূর্ণ সিন্থেসাইজড)।"""
    expr = MUSIC_PRESETS.get(kind)
    if not expr:
        return False
    dur = max(0.5, min(dur + 1.0, 600.0))
    mv.run([mv.FFMPEG, "-y", "-f", "lavfi",
            "-i", f"aevalsrc={expr}:s=44100:d={dur:.2f}",
            "-c:a", "aac", "-b:a", "192k", path])
    return True


# ---- প্রাকৃতিক শব্দ / SFX (সিন্থেসাইজড — সম্পূর্ণ কপিরাইট-ফ্রি) ---------------
# কোনো ইংরেজি শব্দ-প্যাক নেই — ফ্রিকোয়েন্সি দিয়েই বানানো।
# কমা ফিল্টার-গ্রাফ ভেঙে দেয়, তাই \, দিয়ে পালানো।
SFX_EXPR = {
    # পাখি ডাকা — নরম চিরবির, বারে বারে বিভিন্ন সুরে
    "birds": "3.2*(0.055+0.035*sin(2*PI*7.7*t+floor(t*2.3)))*(0.35+0.65*tanh(9*sin(2*PI*1.9*t)))*sin(2*PI*(1850+260*sin(2*PI*14*t))*t)",
    # ঝিঁঝিঁ পোকা — রাতের ঘুম-এর সময়
    "crickets": "(0.045*(0.45+0.55*sin(2*PI*0.31*t)))*if(lt(mod(t\\,0.62)\\,0.34)\\,sin(2*PI*4300*t)*(0.55+0.45*sin(2*PI*23*t))\\,0)",
    # হাওয়ার শ শ শ — বরফ/মরুভূমি
    "wind": "(0.10+0.06*sin(2*PI*0.13*t)+0.03*sin(2*PI*0.41*t))*(0.35*sin(2*PI*85*t)+0.30*sin(2*PI*141*t))",
    # শহরের গুঞ্জ + দূরের হর্ন
    "hum": "0.055*sin(2*PI*118*t)+0.038*sin(2*PI*97.3*t)+0.030*sin(2*PI*236*t)*(0.3+0.7*max(0\\,sin(2*PI*0.43*t)))",
    # মহাকাশ — গভীর কোমল প্যাড
    "space": "0.075*sin(2*PI*108*t)+0.060*sin(2*PI*162.2*t)*(0.6+0.4*sin(2*PI*0.09*t))+0.035*sin(2*PI*324*t)*(0.4+0.6*sin(2*PI*0.05*t))",
    # পায়ের শব্দ — হাঁটা/দৌড়ের সাথে (প্রতি ০.৪৫ সে)
    "steps": "0.30*exp(-22*mod(t\\,0.45))*sin(2*PI*72*t)*lt(mod(t\\,0.45)\\,0.10)",
    # জাদুও ঝিকমিক — জোনাকি/তারার শব্দ
    "sparkle": "(0.055*exp(-5*mod(t\\,0.9)))*sin(2*PI*(1250+950*mod(t\\,0.9))*t)*(0.5+0.5*sin(2*PI*0.5*t))",
    # হাতির ট্রাম্পেট — গভীর-নালি-পাহাড়া (প্রতি ~২.৮ সে)
    "elephant": "if(lt(mod(t\\,2.8)\\,1.1)\\, 0.22*sin(2*PI*(210+90*mod(t*1.6\\,1))*(1+0.35*sin(2*PI*3.1*t)))*(0.75+0.25*sin(2*PI*6.5*t))\\, 0)",
    # বাঘের গর্জন — গভীর-কম্পন (প্রতি ~৩.৫ সে)
    "tiger": "if(lt(mod(t\\,3.5)\\,1.4)\\, 0.30*exp(-0.7*mod(t\\,3.5))*(sin(2*PI*58*t)+0.5*sin(2*PI*89*t)+0.3*sin(2*PI*132*t))\\, 0)",
    # ব্যাঙের ডাক — কুঁড়কুঁড়ে (প্রতি ~১.৬ সে)
    "frog": "if(lt(mod(t\\,1.6)\\,0.5)\\, 0.14*(0.7+0.3*sin(2*PI*9*t))*sin(2*PI*(320+55*sin(2*PI*17*t))*t)\\, 0)",
    # নদীর কলকল — পাথরে-পড়া-পানি (রিভার/পুকুর)
    "river": "(0.07+0.04*sin(2*PI*0.5*t))*(0.4*sin(2*PI*680*t)+0.35*sin(2*PI*1140*t)+0.3*sin(2*PI*1870*t))*(0.6+0.4*sin(2*PI*3.1*t))",
    # আগুনের টিপটিপ — কাঠ-ফাটা পপ
    "fire": "0.17*exp(-26*mod(t*2.9\\,1))*sin(2*PI*(85+130*mod(t*1.9\\,1))*t)*(0.55+0.45*sin(2*PI*2.3*t))",
    # মৌমাছির ভোঁ ভোঁ — ডানার কম্পন
    "bee": "0.11*sin(2*PI*(215+45*sin(2*PI*5.2*t))*t)*(0.55+0.45*sin(2*PI*1.25*t))",
    # হাঁসের ডাক — ক্যাঁক ক্যাঁক (প্রতি ~১.৩৫ সে)
    "duck": "if(lt(mod(t\\,1.35)\\,0.3)\\, 0.17*sin(2*PI*(425+65*mod(t*3.1\\,1))*t)*(0.7+0.3*sin(2*PI*23*t))\\, 0)",
    # ট্রেনের ছক ছক — ছন্দময় চাকা
    "train": "0.15*exp(-8.5*mod(t\\,0.62))*sin(2*PI*92*t)*(0.5+0.5*sin(2*PI*0.5*t))",
    # গাড়ির ইঞ্জিন — ধারাবাহিক গুঞ্জ
    "car": "0.09*sin(2*PI*(84+15*sin(2*PI*0.45*t))*t)+0.05*sin(2*PI*168*t)+0.03*sin(2*PI*252*t)",
    # মন্দিরের ঘণ্টা — দীর্ঘ ঝংকার (প্রতি ~২.২ সে)
    "bell": "if(lt(mod(t\\,2.2)\\,1.3)\\, 0.15*exp(-1.5*mod(t\\,2.2))*(sin(2*PI*640*t)+0.4*sin(2*PI*962*t)+0.25*sin(2*PI*1285*t))\\, 0)",
    # ঢোল/ড্রাম — দুই-ঠোঁট ছন্দ (জন্মদিন/উৎসব)
    "drum": "if(lt(mod(t\\,0.75)\\,0.16)\\, 0.27*exp(-13*mod(t\\,0.75))*sin(2*PI*108*t)\\, if(lt(mod(t\\,0.75)\\,0.34)\\, 0.19*exp(-11*(mod(t\\,0.75)-0.2))*sin(2*PI*140*t)\\, 0))",
    # বজ্রের গর্জন — গভীর ঝড় (প্রতি ~৬.৫ সে) — ভয়ের গল্পের জন্য
    "thunder": "if(lt(mod(t\\,6.5)\\,1.7)\\, 0.30*exp(-1.05*mod(t\\,6.5))*(sin(2*PI*46*t)+0.6*sin(2*PI*71*t)+0.35*sin(2*PI*38*t))*(0.6+0.4*sin(2*PI*8.5*t))\\, 0)",
    # কোকিল — দুই-সুরের কুহু (প্রতি ~২.১ সে)
    "cuckoo": "if(between(mod(t\\,2.1)\\,0\\,0.45)\\, 0.15*sin(2*PI*680*t)*exp(-2.6*mod(t\\,2.1))\\, if(between(mod(t\\,2.1)\\,0.7\\,1.15)\\, 0.15*sin(2*PI*545*t)*exp(-2.6*(mod(t\\,2.1)-0.7))\\, 0))",
    # মোরগের ডাক — কুকুরুকু (প্রতি ~৫.২ সে)
    "rooster": "if(lt(mod(t\\,5.2)\\,1.7)\\, 0.16*sin(2*PI*(470+250*sin(2*PI*2.1*t))*(1+0.4*sin(2*PI*6.8*t)))*(0.6+0.4*sin(2*PI*10.5*t))\\, 0)",
    # কাকের ডাক — ক্যাঁ ক্যাঁ (প্রতি ~২.৬ সে)
    "crow": "if(lt(mod(t\\,2.6)\\,0.5)\\, 0.13*(0.6+0.4*sin(2*PI*14*t))*sin(2*PI*(760+185*sin(2*PI*6.2*t))*t)\\, 0)",
}
SFX_NOISE = {
    "sea":   {"color": "brown", "lowpass": 420, "vol": "(0.12+0.08*sin(2*PI*0.22*t))", "lfo": True},
    "rain":  {"color": "white", "lowpass": 0, "highpass": 900, "vol": "0.055", "lfo": False},
}


def make_sfx(kind: str, dur: float, path: str) -> bool:
    """এক ধরনের প্রাকৃতিক শব্দ বানায় (ক: birds/sea/crickets/wind/hum/space/steps/sparkle/rain)।"""
    kind = str(kind or "").strip()
    d = f"{max(0.4, min(dur, 600.0)):.2f}"

    expr = SFX_EXPR.get(kind)
    if expr:
        mv.run([mv.FFMPEG, "-y", "-f", "lavfi",
                "-i", f"aevalsrc={expr}:s=44100:d={d}",
                "-c:a", "aac", "-b:a", "128k", path])
        return os.path.getsize(path) > 200 if os.path.exists(path) else False

    spec = SFX_NOISE.get(kind)
    if spec:
        chain = []
        if spec.get("lowpass"):
            chain.append(f"lowpass=f={spec['lowpass']}")
        if spec.get("highpass"):
            chain.append(f"highpass=f={spec['highpass']}")
        vol = spec["vol"]
        chain.append(f"volume={vol}:eval=frame")
        mv.run([mv.FFMPEG, "-y", "-f", "lavfi",
                "-i", f"anoisesrc=color={spec['color']}:sample_rate=44100:amplitude=0.5:d={d}",
                "-af", ",".join(chain),
                "-c:a", "aac", "-b:a", "128k", path])
        return os.path.getsize(path) > 200 if os.path.exists(path) else False

    return False


def make_sfx_track(items, durs_ms, total, out_path, workdir, gain=0.9):
    """প্রতি দৃশ্যের SFX-গুলো সঠিক সময়ে এক ট্র্যাকে বসায়।"""
    files = []
    if items:
        os.makedirs(workdir, exist_ok=True)
        for i, kinds in enumerate(list(items)):
            for j, k in enumerate(list(kinds or [])):
                if k not in SFX_EXPR and k not in SFX_NOISE:
                    continue
                dms = durs_ms[i] if i < len(durs_ms) else 0
                if dms <= 0:
                    continue
                p = os.path.join(workdir, f"sfx_{i:03d}_{j}_{k}.m4a")
                if os.path.isfile(p):
                    files.append((p, sum(durs_ms[:i])))
                    continue
                if make_sfx(k, dms / 1000.0, p):
                    files.append((p, sum(durs_ms[:i])))

    if not files:
        return False

    inputs, parts = [], []
    for idx, (fpath, start) in enumerate(files):
        inputs += ["-i", fpath]
        s = max(0, int(start))
        parts.append(f"[{idx}:a]adelay={s}|{s}[a{idx}]")

    n = len(files)
    filt = ";".join(parts) + ";" + "".join(f"[a{i}]" for i in range(n)) + \
           f"amix=inputs={n}:normalize=0:duration=first,atrim=0:{max(1.0, total):.2f}" \
           f",volume={gain}[aout]"
    mv.run([mv.FFMPEG, "-y", *inputs,
            "-filter_complex", filt, "-map", "[aout]",
            "-ar", "44100", "-ac", "1",
            "-f", "mp4", "-c:a", "aac", "-b:a", "128k", out_path])
    return os.path.isfile(out_path) and os.path.getsize(out_path) > 200



# ------------------------------------------------------------------ রেন্ডার
def export_video(src: str, opts: dict) -> dict:
    job = uuid.uuid4().hex[:10]
    work = tempfile.mkdtemp(prefix=f"anim_{job}_")
    try:
        dur = 0.0
        try:
            # আগে আসল ফাইলের দৈর্ঘ্য মাপি (সবচেয়ে নির্ভরযোগ্য)
            dur = ml.probe(src)[0]
        except Exception:  # noqa: BLE001
            dur = 0.0
        if dur <= 0:
            try:
                dur = float(opts.get("dur") or 0)
            except (TypeError, ValueError):
                dur = 0.0
        if dur <= 0:
            dur = 5.0

        # ১) সব ফরম্যাট → পরিষ্কার H.264 (জোড় সংখ্যার সাইজ, yuv420p)
        # skip/exact থাকলে রেকর্ডিংয়ের শুরুর স্থির প্রি-রোল কেটে ভিডিওটা
        # ঠিক অ্যানিমেশনের দৈর্ঘ্য সমান করা হয় (রেকর্ডার নিরাপত্তার জন্য
        # বাড়তি ফ্রেম রাখে — সেগুলো এখানে বাদ পড়ে)
        skip = 0.0
        exact = 0.0
        try:
            skip = max(0.0, float(opts.get("skip") or 0))
        except (TypeError, ValueError):
            skip = 0.0
        try:
            exact = max(0.0, float(opts.get("exact") or 0))
        except (TypeError, ValueError):
            exact = 0.0

        # ১) ফ্রেমই ইতিমধ্যে সঠিক H.264/30fps/জোড়-সাইজ — আবার এনকোড না করে সরাসরি এগোই
        if opts.get("raw_ready"):
            norm = src
        else:
            norm = os.path.join(work, "norm.mp4")
            norm_cmd = [mv.FFMPEG, "-y", "-i", src]
            if skip > 0:
                norm_cmd += ["-ss", f"{skip:.3f}"]
            if exact > 0:
                norm_cmd += ["-t", f"{exact:.3f}"]
            norm_cmd += ["-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2",
                         "-r", "30",
                         "-c:v", "libx264", "-preset", "fast", "-crf", "20",
                         "-pix_fmt", "yuv420p", "-an", norm]
            mv.run(norm_cmd)

        # ২) মিউজিক
        current = norm
        music = (opts.get("music") or "").strip()
        if music in MUSIC_PRESETS:
            mpath = os.path.join(work, "music.m4a")
            make_music(music, dur, mpath)
            muxed = os.path.join(work, "muxed.mp4")
            mv.mux_with_music(current, mpath, dur, muxed,
                              fades=not opts.get("loop"))
            current = muxed

        # ৩) সিমলেস লুপ (boomerang) + পুনরাবৃত্তি
        if opts.get("loop"):
            one = os.path.join(work, "one.mp4")
            try:
                _, has_audio = ml.probe(current)
            except Exception:  # noqa: BLE001
                has_audio = music in MUSIC_PRESETS
            ml.make_boomerang(current, one, has_audio)

            try:
                rep = int(opts.get("repeat") or 1)
            except (TypeError, ValueError):
                rep = 1
            rep = max(1, min(20, rep))

            if rep > 1:
                repf = os.path.join(work, "rep.mp4")
                ml.repeat_file(one, repf, rep)
                current = repf
            else:
                current = one

        out_name = f"anim_{job}.mp4"
        out_path = os.path.join(OUT, out_name)
        shutil.copy(current, out_path)

        try:
            final_dur = ml.probe(out_path)[0]
        except Exception:  # noqa: BLE001
            final_dur = dur

        return {
            "ok": True,
            "url": f"/output/{out_name}",
            "name": out_name,
            "seconds": round(final_dur, 1),
            "base_seconds": round(dur, 1),
            "size_mb": round(os.path.getsize(out_path) / (1024 * 1024), 1),
        }
    finally:
        shutil.rmtree(work, ignore_errors=True)


# ------------------------------------------------------------------ HTTP
class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=WEB, **kw)

    def log_message(self, *args):
        pass

    # --- ভিডিও পাঠানো (Range সাপোর্ট সহ, যাতে সিক করা যায়) ---
    def _serve_video(self, full):
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
        parsed = urlparse(self.path)
        path = parsed.path

        if path.startswith("/output/"):
            full = os.path.join(OUT, os.path.basename(path))
            if os.path.exists(full):
                self._serve_video(full)
                return
            self.send_error(404)
            return

        if path.startswith("/files/"):
            name = os.path.basename(unquote(path))
            full = os.path.join(OUT, name)
            if os.path.exists(full):
                self.send_response(200)
                self.send_header("Content-Type", "application/octet-stream")
                self.send_header(
                    "Content-Disposition", f'attachment; filename="{name}"')
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
        parsed = urlparse(self.path)
        if parsed.path != "/api/export":
            self.send_error(404)
            return

        q = parse_qs(parsed.query)
        ext = (q.get("ext", ["webm"])[0] or "webm").lower()
        if ext not in ("mp4", "webm", "mov"):
            ext = "webm"
        opts = {
            "music": q.get("music", [""])[0],
            "loop": q.get("loop", ["0"])[0] in ("1", "true", "on"),
            "repeat": q.get("repeat", ["1"])[0],
            "dur": q.get("dur", ["0"])[0],
            "skip": q.get("skip", ["0"])[0],
            "exact": q.get("exact", ["0"])[0],
        }

        try:
            length = int(self.headers.get("Content-Length", 0))
            if length <= 0:
                raise ValueError("খালি ফাইল এসেছে।")

            job = uuid.uuid4().hex[:10]
            work = tempfile.mkdtemp(prefix=f"upload_{job}_")
            src = os.path.join(work, f"upload.{ext}")
            try:
                with open(src, "wb") as f:
                    left = length
                    while left > 0:
                        chunk = self.rfile.read(min(1048576, left))
                        if not chunk:
                            break
                        f.write(chunk)
                        left -= len(chunk)
                result = export_video(src, opts)
            finally:
                shutil.rmtree(work, ignore_errors=True)
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
🎬 MithuAnimator চালু হয়েছে!

   👉 ব্রাউজারে খোলো:  http://127.0.0.1:{port}

   অ্যানিমেশন বানাও → Export চাপো → MP4 নামাও।
   সব কিছু তোমার কম্পিউটারেই — ১০০% কপিরাইট-ফ্রি।
   বন্ধ করতে: Ctrl + C
""")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 বন্ধ করা হলো।")


if __name__ == "__main__":
    main()
