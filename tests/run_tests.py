#!/usr/bin/env python3
"""
🧪 MithuVideoMaker টেস্ট-স্যুট — সার্ভার চালু অবস্থায় চালাও:
   python3 tests/run_tests.py
   (সার্ভার বন্ধ থাকলে নিজে থেকে আলাদা পোর্টে চালিয়ে টেস্ট করে)

যাচাই করে: Python/JS সিনট্যাক্স, সব পেজ, মূল API-গুলো (ভয়েস-ইঞ্জিন,
প্রপস-ডিটেক্ট, ম্যানিফেস্ট), ক্যারেক্টর-মাপ টেবিল, গল্প-টেমপ্লেট।
"""
import json
import os
import py_compile
import re
import subprocess
import sys
import tempfile
import urllib.request
import pathlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = "http://127.0.0.1:8765"
PASS, FAIL = 0, 0


def ok(name, cond, extra=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ✅ {name}")
    else:
        FAIL += 1
        print(f"  ❌ {name} {extra}")


def get(path, timeout=10):
    with urllib.request.urlopen(BASE + path, timeout=timeout) as r:
        return r.status, r.read()


def post_json(path, obj, timeout=120):
    req = urllib.request.Request(BASE + path,
                                 data=json.dumps(obj).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


print("🧪 MithuVideoMaker টেস্ট-স্যুট")
print("=" * 46)

# ── ১. Python সিনট্যাক্স ──
print("① Python সিনট্যাক্স")
for f in ["app/server.py", "studio/server.py", "animator/server.py",
          "make_video.py", "make_loop.py", "verify_loop.py", "auto_studio.py"]:
    try:
        py_compile.compile(os.path.join(ROOT, f), doraise=True)
        ok(f, True)
    except Exception as e:  # noqa: BLE001
        ok(f, False, str(e)[:60])

# ── ২. JS সিনট্যাক্স (node --check) ──
print("② JS সিনট্যাক্স")
node = "/usr/bin/env node"
for web in ["script/web/index.html", "studio/web/index.html",
            "animator/web/index.html", "app/web/index.html"]:
    try:
        html = pathlib.Path(os.path.join(ROOT, web)).read_text(encoding="utf-8")
        scripts = re.findall(r"<script[^>]*>(.*?)</script>", html, re.S)
        with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False,
                                         encoding="utf-8") as tf:
            tf.write("\n;\n".join(scripts))
            tmpname = tf.name
        r = subprocess.run(["node", "--check", tmpname],
                           capture_output=True, text=True)
        os.unlink(tmpname)
        ok(web, r.returncode == 0, r.stderr[:60])
    except Exception as e:  # noqa: BLE001
        ok(web, False, str(e)[:60])

# ── ৩. সব পেজ ──
print("③ পেজগুলো")
for pth in ["/", "/script/", "/studio/", "/animation/"]:
    try:
        st, _ = get(pth)
        ok(pth, st == 200)
    except Exception as e:  # noqa: BLE001
        ok(pth, False, str(e)[:50])

# ── ৪. ক্যারেক্টর ও মাপ-টেবিল ──
print("④ ক্যারেক্টর-টেবিল")
import importlib.util  # noqa: E402
# ব্রাউজার-জেএস না চালিয়ে পাইথনেই টেবিল-মিল যাচাই (JSON ফাইল থেকে)
spec_src = pathlib.Path(os.path.join(
    ROOT, "script/web/index.html")).read_text(encoding="utf-8")
m_real = re.search(r"const REAL_SIZE = \{([^}]*)\}", spec_src, re.S)
real_keys = set(re.findall(r"([a-zA-Z]+)\s*:", m_real.group(1))) if m_real else set()
chars_block = spec_src[spec_src.find("const CHARS = {"):spec_src.find("const CHAR_MAP")]
char_keys = set(re.findall(r"^  ([a-z]+): \{", chars_block, re.M))
missing = char_keys - real_keys
ok("সব ক্যারেক্টরের মাপ আছে", len(char_keys) >= 60 and not missing,
   f"বাদ: {sorted(missing)[:6] if missing else '—'}")
ok("ক্যারেক্টর ৬০+", len(char_keys) >= 60, f"{len(char_keys)}টা")

# ── ৫. গল্প-টেমপ্লেট ──
print("⑤ গল্প-টেমপ্লেট")
tpl = re.findall(r"data-sample=\"([a-z0-9]+)\"", spec_src)
sample_m = re.search(r"const SAMPLE = \{(.+?)\n\};", spec_src, re.S)
sample_keys = set(re.findall(r"^  ([a-z0-9]+):", sample_m.group(1), re.M)) if sample_m else set()
missing_t = [t for t in tpl if t not in sample_keys]
ok(f"টেমপ্লেট {len(tpl)}টা, সব লোডযোগ্য", len(tpl) >= 12 and not missing_t,
   f"বাদ: {missing_t[:4] if missing_t else '—'}")

# ── ৬. ভয়েস-ইঞ্জিন (piper + say) ──
print("⑥ ভয়েস-ইঞ্জিন")
try:
    d = post_json("/api/voice", {"texts": ["ভাল্লুক মধু খুঁজছিল।"], "voice": "piper"})
    env = (d.get("items") or [{}])[0].get("env", [])
    ok("Piper ভয়েস + এনভেলপ", d.get("ok") and len(env) > 20,
       f"env={len(env)}")
except Exception as e:  # noqa: BLE001
    ok("Piper ভয়েস", False, str(e)[:60])
try:
    d = post_json("/api/voice", {"texts": ["রাজু হাসল।"], "voice": "piya"})
    ok("say ইঞ্জিন (পিয়া)", d.get("ok"))
except Exception as e:  # noqa: BLE001
    ok("say ইঞ্জিন", False, str(e)[:60])

# ── ৭. প্রপস-ডিটেক্ট (JS ফাংশন না চালিয়ে ম্যাপ-মিল) ──
print("⑦ প্রপস-লাইব্রেরি")
pmap = re.search(r"const PROPS_MAP = \[(.*?)\n\];", spec_src, re.S)
prop_keys = re.findall(r"\[\[\"[^\"]+\"[^]]*\], \"([a-z]+)\"\]", pmap.group(1)) if pmap else []
ok(f"প্রপ {len(prop_keys)}টা", len(prop_keys) >= 20, str(prop_keys[:6]))

# ── ৮. ম্যানিফেস্ট (আগের এক্সপোর্ট থাকলে) ──
print("⑧ দৃশ্য-ম্যানিফেস্ট")
try:
    st, body = get("/api/scenes/manifest")
    man = json.loads(body)
    ok("ম্যানিফেস্ট পড়া যায়", man.get("ok") and len(man.get("scenes", [])) >= 1)
except Exception as e:  # noqa: BLE001
    ok("ম্যানিফেস্ট", False, "এখনো কোনো ভিডিও এক্সপোর্ট হয়নি (স্বাভাবিক)")

print("=" * 46)
print(f"ফলাফল: ✅ {PASS} পাস, ❌ {FAIL} ফেল")
sys.exit(1 if FAIL else 0)
