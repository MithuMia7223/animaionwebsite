#!/usr/bin/env python3
"""
MithuStudio — এক ওয়েবসাইটে সব 🎬

  /            → হোম (দুটো স্টুডিওর দরজা)
  /studio      → ছবি থেকে ভিডিও (slideshow + music + loop)
  /animation   → কীফ্রেম অ্যানিমেশন স্টুডিও (shapes, emoji, particles, easing)
  /output/...  → তৈরি ভিডিও
  /files/...   → ডাউনলোড

চালাও:  python3 app/server.py
খোলো:   http://127.0.0.1:8765
"""
import array
import base64
import json
import math
import mimetypes
import os
import shutil
import subprocess
import sys
import time
import uuid
import wave
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, unquote, urlparse

ROOT = os.path.dirname(os.path.abspath(__file__))          # .../app
PROJECT = os.path.dirname(ROOT)                            # .../MithuVideoMaker
sys.path.insert(0, PROJECT)

from studio import server as slideshow      # noqa: E402
from animator import server as animator     # noqa: E402

OUT = os.path.join(ROOT, "output")
WEB = os.path.join(ROOT, "web")
DATA = os.path.join(ROOT, "data")
os.makedirs(OUT, exist_ok=True)
os.makedirs(DATA, exist_ok=True)
CHAR_FILE = os.path.join(DATA, "characters.json")

# দুটো স্টুডিও এখন একই output ফোল্ডারে লিখবে
slideshow.OUT = OUT
animator.OUT = OUT

PORT = 8765

# ---- ভয়েস (ম্যাকের নিজের TTS — ইন্টারনেট ছাড়াই) ----
VOICE_DIR = os.path.join(OUT, "_voice")
os.makedirs(VOICE_DIR, exist_ok=True)
VOICE_NAMES = {
    "piya": "Piya",        # বাংলা
    "samantha": "Samantha",
    "rishi": "Rishi",
    "tara": "Tara",
}

# ক্যারেক্টার অনুযায়ী গলার পিচ (asetrate × p, লম্বা মিটিয়ে atempo দিয়ে ফেরাই)
TONE_PITCH = {
    "child": 1.30,   # শিশু
    "girl": 1.10,    # মেয়ে
    "boy": 0.92,     # মানুষ/ছেলে
    "small": 1.45,   # ছোট প্রাণী (বিড়াল/খরগোশ/পাখি)
    "big": 0.78,     # বড় প্রাণী (হাতি/বাঘ/সিংহ)
    "robot": 0.95,   # রোবট
    "ghost": 0.72,   # ভূত
}
TONE_FX = {
    "robot": "tremolo=f=7:d=0.85",
    "ghost": "tremolo=f=4.5:d=0.9",
    "alien": "tremolo=f=6:d=0.85",
}


def apply_tone(wav, tone):
    """ভয়েসে ক্যারেক্টার-গলার পিচ/ইফেক্ট বসায় (in-place)।"""
    tone = (tone or "").strip()
    p = TONE_PITCH.get(tone)
    if not p:
        return
    tmp = wav + ".tone.wav"
    chain = f"asetrate={int(44100 * p)},atempo={1.0 / p:.4f}"
    fx = TONE_FX.get(tone)
    if fx:
        chain += "," + fx
    try:
        animator.mv.run([animator.mv.FFMPEG, "-y", "-i", wav,
                         "-af", chain, "-ar", "44100", "-ac", "1", tmp])
        if os.path.getsize(tmp) > 200:
            os.replace(tmp, wav)
    except Exception:  # noqa: BLE001
        pass
    finally:
        if os.path.exists(tmp):
            try:
                os.remove(tmp)
            except OSError:
                pass


def wav_envelope(path, fps=30):
    """wav থেকে ভলিউম এনভেলপ (০..১) — ক্যারেক্টারের ঠোঁট নাড়ানোর জন্য।

    প্রতি সেকেন্ডে ৩০টা মান, তাই ভিডিওর লিপ সিঙ্ক ফ্রেম-সঠিক হয়।
    """
    try:
        with wave.open(path, "rb") as w:
            ch = w.getnchannels()
            sw = w.getsampwidth()
            rate = w.getframerate()
            raw = w.readframes(w.getnframes())
    except Exception:  # noqa: BLE001
        return []

    if sw != 2 or rate <= 0 or not raw:
        return []

    arr = array.array("h")
    arr.frombytes(raw)
    if ch > 1:
        arr = arr[::ch]

    step = max(1, int(rate / fps))
    vals = []
    peak = 0.0
    for i in range(0, len(arr) - step + 1, step):
        seg = arr[i:i + step]
        if not seg:
            break
        total = 0
        for v in seg:
            total += v * v
        rms = math.sqrt(total / len(seg)) / 32768.0
        vals.append(rms)
        if rms > peak:
            peak = rms

    if peak <= 0:
        return []

    out = []
    for v in vals:
        r = v / peak
        # খুব হালকা আওয়াজে মুখ বন্ধ রাখি
        out.append(0.0 if r < 0.05 else round(min(1.0, math.sqrt(r)), 2))
    return out


def make_voice(texts, voice, tones=None):
    """প্রতি দৃশ্যের জন্য আলাদা অডিও — যাতে টাইমিং মিলিয়ে ভিডিও বানানো যায়।
    tones = প্রতি দৃশ্যের স্পিকারের গলা (child/girl/boy/small/big/robot/ghost)।"""
    # পুরোনো ভয়েস ফাইল পরিষ্কার (১ দিনের বেশি)
    try:
        now = time.time()
        for name in os.listdir(VOICE_DIR):
            full = os.path.join(VOICE_DIR, name)
            if os.path.isdir(full) and now - os.path.getmtime(full) > 86400:
                shutil.rmtree(full, ignore_errors=True)
    except Exception:  # noqa: BLE001
        pass

    job = uuid.uuid4().hex[:10]
    folder = os.path.join(VOICE_DIR, job)
    os.makedirs(folder, exist_ok=True)

    items = []
    total = 0.0

    for i, t in enumerate(list(texts)[:60]):
        txt = " ".join(str(t or "").split())
        if not txt:
            items.append({"i": i, "dur": 0.0})
            continue

        aiff = os.path.join(folder, f"v{i:03d}.aiff")
        wav = os.path.join(folder, f"v{i:03d}.wav")

        ok = False
        for cmd in (["say", "-v", voice, "-o", aiff, txt],
                    ["say", "-o", aiff, txt]):
            try:
                p = subprocess.run(cmd, capture_output=True, timeout=120)
                if p.returncode == 0 and os.path.exists(aiff):
                    ok = True
                    break
            except Exception:  # noqa: BLE001
                pass

        if not ok:
            items.append({"i": i, "dur": 0.0})
            continue

        try:
            animator.mv.run([animator.mv.FFMPEG, "-y", "-i", aiff,
                             "-ar", "44100", "-ac", "1", wav])
            apply_tone(wav, (tones or [None] * len(texts))[i] if i < len(tones or []) else None)
            d = animator.ml.probe(wav)[0]
            env = wav_envelope(wav)
        except Exception:  # noqa: BLE001
            d = 0.0
            env = []

        items.append({"i": i, "dur": round(d, 3), "env": env})
        total += d

    return {"ok": True, "job": job, "items": items, "total": round(total, 2)}


def build_voice_mix(job, durs_ms, music, total, out_path, sfx=None):
    """দৃশ্যের অডিওগুলো সঠিক সময়ে বসিয়ে (+ প্রাকৃতিক শব্দ + ঐচ্ছিক মিউজিক) একটা ট্র্যাক বানায়।"""
    folder = os.path.join(VOICE_DIR, job)
    if not os.path.isdir(folder):
        return False

    files = [n for n in sorted(os.listdir(folder))
             if n.startswith("v") and n.endswith(".wav")]
    if not files:
        return False

    inputs = []
    parts = []
    for idx, fname in enumerate(files):
        # ফাইলের নাম থেকেই দৃশ্য-নম্বর (v003.wav → ৩) — কোনো দৃশ্যের TTS
        # ফেল করলে তার wav থাকে না, তবু পরের দৃশ্যগুলোর সময় সরে যাবে না
        try:
            si = int(fname[1:4])
        except ValueError:
            si = idx
        start = sum(durs_ms[:si]) if si < len(durs_ms) else 0
        start = max(0, int(start))
        inputs += ["-i", os.path.join(folder, fname)]
        parts.append(f"[{idx}:a]adelay={start}|{start}[a{idx}]")

    total = max(1.0, total)

    # প্রাকৃতিক শব্দ (SFX) — প্রতি দৃশ্যে যা যা লাগবে
    sfx_items = list(sfx or [])
    if any(sfx_items):
        spath0 = os.path.join(folder, "sfxtrack.m4a")
        sdir = os.path.join(folder, "sfx")
        sdurs = list(durs_ms)[:len(sfx_items)]
        sdurs += [0] * (len(sfx_items) - len(sdurs))
        if animator.make_sfx_track(sfx_items, sdurs, total, spath0, sdir):
            inputs += ["-i", spath0]
            sx = len(inputs) // 2 - 1     # ফাইল-ইনপুট নম্বর ("-i" জোড়ার অর্ধেক)
            parts.append(f"[{sx}:a]adelay=0|0[a{sx}]")

    n = len(files)
    nid = len(inputs) // 2          # inputs = ["-i", পাথ, "-i", পাথ...]
    filt = ";".join(parts) + ";" + "".join(f"[a{i}]" for i in range(nid)) + \
           f"amix=inputs={nid}:normalize=0:duration=longest[voice]"

    cmd = [animator.mv.FFMPEG, "-y", *inputs]

    if music and music in animator.MUSIC_PRESETS:
        mpath = os.path.join(folder, "music.m4a")
        animator.make_music(music, total, mpath)
        cmd += ["-i", mpath]
        filt += (f";[{nid}:a]volume=0.28[m];"
                 "[voice][m]amix=inputs=2:normalize=0:duration=first[mix]")
        label = "mix"
    else:
        label = "voice"

    # শেষ দৃশ্যের পরেও অডিও ট্র্যাক ভিডিওর সমান লম্বা রাখি (নইলে শেষটা কাটা পড়ে)
    filt += f";[{label}]apad=pad_dur={total:.2f},atrim=0:{total:.2f}[aout]"

    cmd += ["-filter_complex", filt, "-map", "[aout]",
            "-t", f"{total:.2f}",
            "-c:a", "aac", "-b:a", "192k", out_path]
    animator.mv.run(cmd)
    return True

# URL প্রিফিক্স → ফোল্ডার
APPS = {
    "/studio": os.path.join(PROJECT, "studio", "web"),
    "/animation": os.path.join(PROJECT, "animator", "web"),
    "/script": os.path.join(PROJECT, "script", "web"),
}

# ---- ফ্রেম-বাই-ফ্রেম এক্সপোর্ট -------------------------------------------
# ব্রাউজার প্রতিটা ফ্রেম JPEG করে পাঠায়, ffmpeg সেগুলো দিয়ে হুবহু ৩০ fps
# ভিডিও বানায়। ট্যাব লুকানো থাকলেও কাজ করে, ফ্রেম মিস হয় না।
FRAME_ROOT = os.path.join(OUT, "_frames")
os.makedirs(FRAME_ROOT, exist_ok=True)


def _parse_durs(raw):
    out = []
    for part in (raw or "").split(","):
        part = part.strip()
        if not part:
            continue
        try:
            out.append(int(float(part)))
        except ValueError:
            out.append(0)
    return out


def _parse_sfx(raw):
    """SFX-কোয়েরি পার্স — প্রতি দৃশ্যের কিন্ড-তালিকা।

    ফরম্যাট: `birds,steps|crickets||sea` — দৃশ্য আলাদা `|`, কিন্ড আলাদা কমা।
    """
    out = []
    for part in (raw or "").split("|"):
        kinds = [k.strip() for k in part.split(",") if k.strip()]
        out.append(kinds)
    return out


def frames_start():
    job = uuid.uuid4().hex[:10]
    os.makedirs(os.path.join(FRAME_ROOT, job), exist_ok=True)

    # পুরোনো ফ্রেম ফোল্ডার পরিষ্কার (১ দিনের বেশি)
    try:
        now = time.time()
        for name in os.listdir(FRAME_ROOT):
            full = os.path.join(FRAME_ROOT, name)
            if os.path.isdir(full) and now - os.path.getmtime(full) > 86400:
                shutil.rmtree(full, ignore_errors=True)
    except Exception:  # noqa: BLE001
        pass

    return {"ok": True, "job": job}


def chars_load():
    """নিজের বানানো ক্যারেক্টার — সরাসরি প্রজেক্ট ফোল্ডারে সেভ থাকে।"""
    try:
        with open(CHAR_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:  # noqa: BLE001
        return {}


def chars_save(data):
    os.makedirs(DATA, exist_ok=True)
    tmp = CHAR_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    os.replace(tmp, CHAR_FILE)
    return {"ok": True, "count": len(data)}


def frames_save(job, i, data, b64=False):
    folder = os.path.join(FRAME_ROOT, os.path.basename(job))
    if not os.path.isdir(folder):
        return {"ok": False, "error": "এই জব পাওয়া যায়নি"}
    if b64:
        try:
            data = base64.b64decode(data)
        except Exception:  # noqa: BLE001
            return {"ok": False, "error": "ফ্রেম ডিকোড হয়নি"}
    if not data:
        return {"ok": False, "error": "খালি ফ্রেম"}
    with open(os.path.join(folder, f"f{int(i):05d}.jpg"), "wb") as f:
        f.write(data)
    return {"ok": True}


def _mix_music_sfx(sfx, durs_ms, music, total, out_path):
    """ভয়েস ছাড়া রেন্ডার — SFX (+ঐচ্ছিক মিউজিক) এক ট্র্যাক বানায়।"""
    folder = os.path.dirname(out_path)
    items = list(sfx or [])
    sdurs = [int(d) for d in (durs_ms or []) if d]
    if not sdurs:
        # দৃশ্য-দৈর্ঘ্য নেই — পুরো সময় সমান ভাগ করে নিই
        nsc = max(1, len(items))
        piece = max(600, int(total * 1000 / nsc))
        sdurs = [piece] * nsc
    sdurs += [0] * (len(items) - len(sdurs))
    has_music = bool(music and music in animator.MUSIC_PRESETS)

    spath = os.path.join(folder, "sfxtrack.m4a")
    ok = animator.make_sfx_track(items, sdurs, total, spath, folder)
    if not ok and not has_music:
        return False

    inputs, filt_parts = [], []
    idx = 0
    if ok:
        inputs += ["-i", spath]
        idx = 1
    if has_music:
        mpath = os.path.join(folder, "mmusic.m4a")
        animator.make_music(music, total, mpath)
        inputs += ["-i", mpath]
    total = max(1.0, total)
    if ok and has_music:
        filt = (f"[0:a]atrim=0:{total:.2f}[s];"
                f"[1:a]volume=0.30,atrim=0:{total:.2f}[m];"
                "[s][m]amix=inputs=2:normalize=0:duration=first,apad=pad_dur=1.0,"
                f"atrim=0:{total:.2f}[aout]")
    elif ok:
        filt = f"[0:a]apad=pad_dur=1.0,atrim=0:{total:.2f}[aout]"
    else:
        filt = f"[0:a]volume=0.30,apad=pad_dur=1.0,atrim=0:{total:.2f}[aout]"

    animator.mv.run([animator.mv.FFMPEG, "-y", *inputs,
                     "-filter_complex", filt, "-map", "[aout]",
                     "-t", f"{total:.2f}",
                     "-c:a", "aac", "-b:a", "192k", out_path])
    return os.path.isfile(out_path) and os.path.getsize(out_path) > 200


_VT_CACHE = None


def _vt_available():
    """এই ffmpeg-এ Mac-এর GPU এনকোডার (h264_videotoolbox) আছে কি না — একবারই দেখি।"""
    global _VT_CACHE
    if _VT_CACHE is None:
        try:
            out = subprocess.run(
                [animator.mv.FFMPEG, "-hide_banner", "-encoders"],
                capture_output=True, text=True, timeout=10).stdout
            _VT_CACHE = "h264_videotoolbox" in out
        except Exception:  # noqa: BLE001
            _VT_CACHE = False
    return _VT_CACHE


def frames_finish(job, fps, opts, voice_job, durs, music, total, sfx=None):
    folder = os.path.join(FRAME_ROOT, os.path.basename(job))
    if not os.path.isdir(folder):
        return {"ok": False, "error": "এই জব পাওয়া যায়নি"}

    frames = sorted(n for n in os.listdir(folder) if n.endswith(".jpg"))
    if not frames:
        return {"ok": False, "error": "কোনো ফ্রেম আসেনি"}

    # ⚡ দ্রুত মোড — Mac-এর GPU (videotoolbox) দিয়ে এনকোড; না থাকলে নিজেই CPU-তে নামে
    fast = str(opts.get("fast") or "") in ("1", "true", "yes")
    vt = _vt_available() if fast else False
    if vt:
        venc = ["-c:v", "h264_videotoolbox", "-b:v", "7M",
                "-maxrate", "10M", "-bufsize", "14M", "-pix_fmt", "yuv420p"]
    else:
        venc = ["-c:v", "libx264", "-preset", "fast", "-crf", "20",
                "-pix_fmt", "yuv420p"]

    # ffmpeg-এর image2 সিরিজে মাঝে ফাঁক থাকলে সেখানেই থেমে যায় — তাই
    # ফাইলগুলো পুনঃক্রমাঙ্কন করে ফাঁক বন্ধ করি (এক্সপোর্ট নষ্ট হওয়ার শেষ ভরসা)
    def _fidx(name):
        try:
            return int(name[1:6])
        except ValueError:
            return None

    if any(_fidx(name) != i for i, name in enumerate(frames)):
        staged = [(f"_r{i:05d}.jpg", name) for i, name in enumerate(frames)]
        for newname, oldname in staged:
            os.replace(os.path.join(folder, oldname),
                       os.path.join(folder, newname))
        for i, (newname, _) in enumerate(staged):
            os.replace(os.path.join(folder, newname),
                       os.path.join(folder, f"f{i:05d}.jpg"))

    work = os.path.join(OUT, f"_tmp_{job}")
    os.makedirs(work, exist_ok=True)
    raw = os.path.join(work, "raw.mp4")

    animator.mv.run([
        animator.mv.FFMPEG, "-y",
        "-framerate", str(max(1, int(fps))),
        "-i", os.path.join(folder, "f%05d.jpg"),
    ] + venc + [raw])

    # GPU এনকোডার চলতে গিয়ে ফেল করলে (কিছু Mac-এ থাকে না) — CPU-তে আবার
    if vt and (not os.path.isfile(raw) or os.path.getsize(raw) < 1000):
        try:
            animator.mv.run([
                animator.mv.FFMPEG, "-y",
                "-framerate", str(max(1, int(fps))),
                "-i", os.path.join(folder, "f%05d.jpg"),
                "-c:v", "libx264", "-preset", "fast", "-crf", "20",
                "-pix_fmt", "yuv420p", raw,
            ])
        except Exception:  # noqa: BLE001
            pass

    # ভয়েস থাকলে মিউজিক পরে মেশানো হবে; SFX থাকলেও নিজের হাতে মেশাই
    opts = dict(opts)
    opts["music"] = "" if (voice_job or any(list(sfx or []))) else music
    opts["loop"] = False
    opts["repeat"] = 1
    opts["dur"] = f"{max(1.0, total):.2f}"
    opts["raw_ready"] = True   # raw.mp4 ইতিমধ্যে পরিষ্কার H.264 — আবার এনকোড নয়

    res = animator.export_video(raw, opts)

    if not voice_job and res.get("ok") and any(list(sfx or [])):
        # ভয়েস নেই কিন্তু SFX (+মিউজিক) আছে — নিজের হাতে সাউন্ড ট্র্যাক
        out_path = os.path.join(OUT, res["name"])
        base = float(res.get("base_seconds") or 0) or total
        mix = os.path.join(OUT, f"_tmp_{job}")
        os.makedirs(mix, exist_ok=True)
        mix = os.path.join(mix, "sndmix.m4a")
        if _mix_music_sfx(sfx, durs, music, base, mix):
            voiced = os.path.join(OUT, f"_tmp_{job}", "sfxed.mp4")
            animator.mv.mux_with_music(out_path, mix, base, voiced)
            shutil.copy(voiced, out_path)
            res["size_mb"] = round(os.path.getsize(out_path) / (1024 * 1024), 1)
            shutil.rmtree(os.path.join(OUT, f"_tmp_{job}"), ignore_errors=True)

    if voice_job and res.get("ok"):
        out_path = os.path.join(OUT, res["name"])
        base = float(res.get("base_seconds") or 0)
        if base <= 0:
            try:
                base = animator.ml.probe(out_path)[0]
            except Exception:  # noqa: BLE001
                base = total

        mix = os.path.join(work, "voicemix.m4a")
        if base > 0 and build_voice_mix(voice_job, durs, music, base, mix, sfx=sfx):
            voiced = os.path.join(work, "voiced.mp4")
            animator.mv.mux_with_music(out_path, mix, base, voiced, fades=False)
            shutil.copy(voiced, out_path)
            res["size_mb"] = round(os.path.getsize(out_path) / (1024 * 1024), 1)
            res["voiced"] = True
            shutil.rmtree(os.path.join(VOICE_DIR, voice_job), ignore_errors=True)
        else:
            res["voiced"] = False

    shutil.rmtree(work, ignore_errors=True)
    shutil.rmtree(folder, ignore_errors=True)
    return res


def _send_file(handler, full, download=False):
    """ফাইল পাঠানো — mp4 হলে Range সাপোর্ট (সিক করার জন্য)।"""
    if not os.path.isfile(full):
        handler.send_error(404)
        return

    size = os.path.getsize(full)
    ctype = mimetypes.guess_type(full)[0] or "application/octet-stream"

    if download:
        handler.send_response(200)
        handler.send_header("Content-Type", "application/octet-stream")
        handler.send_header(
            "Content-Disposition",
            f'attachment; filename="{os.path.basename(full)}"')
        handler.send_header("Content-Length", str(size))
        handler.end_headers()
        with open(full, "rb") as f:
            shutil.copyfileobj(f, handler.wfile)
        return

    start, end = 0, size - 1
    partial = False
    rng = handler.headers.get("Range")

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
        handler.send_response(416)
        handler.send_header("Content-Range", f"bytes */{size}")
        handler.send_header("Content-Length", "0")
        handler.end_headers()
        return

    length = end - start + 1
    handler.send_response(206 if partial else 200)
    handler.send_header("Content-Type", ctype)
    handler.send_header("Accept-Ranges", "bytes")
    handler.send_header("Content-Length", str(length))
    if partial:
        handler.send_header("Content-Range", f"bytes {start}-{end}/{size}")
    handler.end_headers()

    with open(full, "rb") as f:
        f.seek(start)
        left = length
        while left > 0:
            chunk = f.read(min(262144, left))
            if not chunk:
                break
            handler.wfile.write(chunk)
            left -= len(chunk)


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *args):
        pass

    def _foreign_host(self):
        """DNS-rebinding ঠেকাই — শুধু লোকাল হোস্টনেম মেনে নেই।"""
        host = (self.headers.get("Host") or "").split(":")[0].strip()
        if host and host not in ("127.0.0.1", "localhost", "::1"):
            self.send_error(403)
            return True
        return False

    # ---------------- GET ----------------
    def do_GET(self):
        if self._foreign_host():
            return
        path = unquote(urlparse(self.path).path)

        if path == "/api/chars":
            body = json.dumps({"ok": True, "chars": chars_load()},
                              ensure_ascii=False).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        if path.startswith("/output/"):
            _send_file(self, os.path.join(OUT, os.path.basename(path)))
            return

        # ভয়েস-প্রিভিউ — প্রতি দৃশ্যের WAV (পুরো ফোল্ডার নয়, শুধু ভেতরের ফাইল)
        if path.startswith("/voice/"):
            rel = unquote(path[len("/voice/"):])
            full = os.path.abspath(os.path.join(VOICE_DIR, rel))
            if full.startswith(os.path.abspath(VOICE_DIR) + os.sep) and os.path.isfile(full):
                _send_file(self, full)
            else:
                self.send_error(404)
            return

        if path.startswith("/files/"):
            _send_file(self, os.path.join(OUT, os.path.basename(path)),
                       download=True)
            return

        if path in ("/", "/index.html"):
            _send_file(self, os.path.join(WEB, "index.html"))
            return

        for prefix, folder in APPS.items():
            if path == prefix or path.startswith(prefix + "/"):
                if path == prefix:
                    # ট্রেলিং-স্ল্যাশ ছাড়া পেজে relative অ্যাসেট (fonts/ ইত্যাদি)
                    # ভুল জায়গায় যায় — তাই স্ল্যাশসহ ঠিকানায় পাঠিয়ে দিই
                    self.send_response(301)
                    self.send_header("Location", prefix + "/")
                    self.send_header("Content-Length", "0")
                    self.end_headers()
                    return
                rest = path[len(prefix):].lstrip("/") or "index.html"
                full = os.path.normpath(os.path.join(folder, rest))
                if not full.startswith(os.path.abspath(folder) + os.sep):
                    self.send_error(403)
                    return
                _send_file(self, full)
                return

        self.send_error(404)

    # ---------------- POST ----------------
    def do_POST(self):
        if self._foreign_host():
            return
        parsed = urlparse(self.path)
        path = parsed.path

        try:
            if path == "/api/chars":
                length = int(self.headers.get("Content-Length", 0))
                payload = json.loads(self.rfile.read(length) or b"{}")
                chars = payload.get("chars") or {}
                if not isinstance(chars, dict):
                    raise ValueError("chars অবজেক্ট হতে হবে")
                result = chars_save(chars)

            elif path == "/api/snap":
                # প্রিভিউ ফ্রেম সেভ (ডিবাগ / থাম্বনেইল)
                length = int(self.headers.get("Content-Length", 0))
                data = self.rfile.read(length) if length > 0 else b""
                name = f"snap_{uuid.uuid4().hex[:8]}.png"
                with open(os.path.join(OUT, name), "wb") as f:
                    f.write(data)
                result = {"ok": True, "name": name, "url": f"/output/{name}",
                          "size": len(data)}

            elif path == "/api/generate":
                length = int(self.headers.get("Content-Length", 0))
                payload = json.loads(self.rfile.read(length) or b"{}")
                result = slideshow.build(payload)

            elif path == "/api/frames/start":
                result = frames_start()

            elif path == "/api/frames":
                q = parse_qs(parsed.query)
                job = (q.get("job", [""])[0] or "").strip()
                idx = int(q.get("i", ["0"])[0] or 0)
                is_b64 = (q.get("b64", ["0"])[0] or "0") == "1"
                length = int(self.headers.get("Content-Length", 0))
                data = self.rfile.read(length) if length > 0 else b""
                if is_b64:
                    data = data.strip()
                result = frames_save(job, idx, data, is_b64)

            elif path == "/api/frames/finish":
                q = parse_qs(parsed.query)
                result = frames_finish(
                    (q.get("job", [""])[0] or "").strip(),
                    int(float((q.get("fps", ["30"])[0] or 30))),
                    {
                        "crf": "20",
                        "size": q.get("size", ["1080"])[0],
                        "fast": q.get("fast", [""])[0],
                    },
                    (q.get("vjob", [""])[0] or "").strip(),
                    _parse_durs((q.get("vdurs", [""])[0] or "")),
                    q.get("music", [""])[0],
                    float((q.get("dur", ["0"])[0] or 0)),
                    sfx=_parse_sfx((q.get("sfx", [""])[0] or "")),
                )

            elif path == "/api/voice":
                length = int(self.headers.get("Content-Length", 0))
                payload = json.loads(self.rfile.read(length) or b"{}")
                voice = VOICE_NAMES.get((payload.get("voice") or "piya").lower(), "Piya")
                result = make_voice(payload.get("texts") or [], voice,
                                    tones=payload.get("tones"))

            elif path == "/api/export":
                result = self._handle_animation(parse_qs(parsed.query))

            else:
                self.send_error(404)
                return

        except Exception as e:  # noqa: BLE001
            result = {"ok": False, "error": f"{type(e).__name__}: {e}"}

        body = json.dumps(result, ensure_ascii=False).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _handle_animation(self, q):
        ext = (q.get("ext", ["webm"])[0] or "webm").lower()
        if ext not in ("mp4", "webm", "mov"):
            ext = "webm"

        voice_job = (q.get("vjob", [""])[0] or "").strip()
        sfx = _parse_sfx((q.get("sfx", [""])[0] or ""))
        music = q.get("music", [""])[0]

        opts = {
            # ভয়েস/এসএফএক্স থাকলে মিউজিক পরে মেশানো হবে
            "music": "" if (voice_job or any(list(sfx or []))) else music,
            "loop": q.get("loop", ["0"])[0] in ("1", "true", "on"),
            "repeat": q.get("repeat", ["1"])[0],
            "dur": q.get("dur", ["0"])[0],
            "skip": q.get("skip", ["0"])[0],
            "exact": q.get("exact", ["0"])[0],
            # ব্রাউজার-এনকোড করা WebCodecs MP4 ইতিমধ্যেই পরিষ্কার H.264 — পুনঃএনকোড নয়
            "raw_ready": q.get("raw_ready", ["0"])[0] == "1",
        }

        length = int(self.headers.get("Content-Length", 0))
        if length <= 0:
            return {"ok": False, "error": "খালি ফাইল এসেছে।"}

        job = uuid.uuid4().hex[:10]
        work = os.path.join(OUT, f"_tmp_{job}")
        os.makedirs(work, exist_ok=True)
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

            res = animator.export_video(src, opts)

            # ---- দৃশ্য-দৈর্ঘ্যের তালিকা — ভয়েস ও এসএফএক্স দুটোতেই লাগে
            raw = (q.get("vdurs", [""])[0] or "").strip()
            durs = []
            for part in raw.split(","):
                part = part.strip()
                if not part:
                    continue
                try:
                    durs.append(int(float(part)))
                except ValueError:
                    durs.append(0)

            out_path = os.path.join(OUT, res["name"]) if res.get("ok") else None
            total = 0
            if out_path and res.get("ok"):
                total = float(res.get("base_seconds") or 0)
                if total <= 0:
                    try:
                        total = animator.ml.probe(out_path)[0]
                    except Exception:  # noqa: BLE001
                        total = 0

            # ---- ভয়েস নেই কিন্তু SFX (+মিউজিক) আছে — নিজের হাতে সাউন্ড ট্র্যাক
            if not voice_job and res.get("ok") and any(list(sfx or [])) and total > 0:
                mix = os.path.join(work, "sndmix.m4a")
                if _mix_music_sfx(sfx, durs, music, total, mix):
                    voiced = os.path.join(work, "sfxed.mp4")
                    animator.mv.mux_with_music(out_path, mix, total, voiced)
                    shutil.copy(voiced, out_path)
                    res["size_mb"] = round(
                        os.path.getsize(out_path) / (1024 * 1024), 1)

            # ---- ভয়েস বসানো
            if voice_job and res.get("ok"):
                mix = os.path.join(work, "voicemix.m4a")
                if total > 0 and build_voice_mix(voice_job, durs, music, total,
                                                 mix, sfx=sfx):
                    voiced = os.path.join(work, "voiced.mp4")
                    animator.mv.mux_with_music(out_path, mix, total, voiced,
                                               fades=False)
                    shutil.copy(voiced, out_path)
                    res["size_mb"] = round(
                        os.path.getsize(out_path) / (1024 * 1024), 1)
                    res["voiced"] = True
                    shutil.rmtree(os.path.join(VOICE_DIR, voice_job),
                                  ignore_errors=True)
                else:
                    res["voiced"] = False

            return res
        finally:
            shutil.rmtree(work, ignore_errors=True)


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else PORT
    srv = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"""
🎬 MithuStudio চালু হয়েছে!

   👉 হোম:        http://127.0.0.1:{port}/
   📝  স্ক্রিপ্ট:   http://127.0.0.1:{port}/script
   🖼️  ভিডিও:      http://127.0.0.1:{port}/studio
   ✨  অ্যানিমেশন:  http://127.0.0.1:{port}/animation

   সব কিছু তোমার কম্পিউটারেই তৈরি হয় — কোনো API, সাবস্ক্রিপশন বা ওয়াটারমার্ক নেই।
   বন্ধ করতে: Ctrl + C
""")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 বন্ধ করা হলো।")


if __name__ == "__main__":
    main()
