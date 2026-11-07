# 🔁 ADVANCED LOOP SCRIPT — "ম্যাজিক আয়না" (The Magic Mirror)
## প্রো-লেভেল সিমলেস লুপ · মাল্টি-লেয়ার · ড্রোস্টে জুম

**ফরম্যাট:** 9:16 (Shorts/Reels) — 16:9 ভার্সনও দেওয়া আছে
**দৈর্ঘ্য:** ২৪ সেকেন্ড (576 ফ্রেম @ 24fps)
**টেম্পো:** ১২০ BPM → ৪৮ beat → ১২ bar (হুবহু মিলে যায়!)
**স্টাইল:** Pixar-ধাঁচ 3D, নিওন-প্যাস্টেল কিডস রুম
**লক্ষ্য:** 🎯 একবার দেখলে চোখ সরাতে পারবে না — লুপ টেরই পাবে না

---

# 🧠 PART 0 — অ্যাডভান্সড লুপের ৬টা আর্কিটাইপ

| # | আর্কিটাইপ | কীভাবে seamless হয় | কঠিনতা |
|---|---|---|---|
| 1 | **Match Cut Loop** | শেষ শট আর প্রথম শট হুবহু একই কম্পোজিশন | ⭐⭐ |
| 2 | **Whip Pan Loop** | দ্রুত ডানে প্যান → ঝাপসা ফ্রেমে কাট → আবার শুরু | ⭐⭐⭐ |
| 3 | **Cover Wipe Loop** | কোনো বস্তু ক্যামেরার সামনে দিয়ে যায় → কাট ঢেকে দেয় | ⭐⭐ |
| 4 | **Droste / Zoom Loop** | ক্যামেরা আয়নায় ঢুকে যায় → ভেতরে আবার একই দৃশ্য | ⭐⭐⭐⭐⭐ |
| 5 | **Palindromic Loop** | সামনে → উল্টো (boomerang) — গণিতের নিখুঁত লুপ | ⭐ |
| 6 | **Parallax Layer Loop** | ৩টা লেয়ার আলাদা গতিতে লুপ → গভীরতা + মন mesmerized | ⭐⭐⭐⭐ |

**এই স্ক্রিপ্টে ৪ + ৬ + ১ একসাথে ব্যবহার করা হবে** — সবচেয়ে শক্তিশালী কম্বো।

---

# 📐 PART 1 — টাইমিং ম্যাথ (প্রোডাকশনের ভিত্তি)

```
দৈর্ঘ্য      : 24.000 সেকেন্ড
ফ্রেমরেট     : 24 fps
মোট ফ্রেম    : 24 × 24 = 576 ফ্রেম
টেম্পো       : 120 BPM  →  1 beat = 0.5s = 12 ফ্রেম
মোট beat     : 24 / 0.5 = 48 beat = 12 bar (4/4)
প্রতি শট      : 2 bar = 4s = 96 ফ্রেম
মোট শট       : 6টা
```

> ✅ **সব সংখ্যা পূর্ণ** — তাই কোনো শট মাঝ-beat-এ কাটবে না। এটাই প্রো লুপের প্রথম শর্ত।

## ফ্রেম-অ্যাকুরেট কাট পয়েন্ট
| শট | শুরু (s) | শেষ (s) | ফ্রেম |
|---|---|---|---|
| 1 | 0.000 | 4.000 | 0–95 |
| 2 | 4.000 | 8.000 | 96–191 |
| 3 | 8.000 | 12.000 | 192–287 |
| 4 | 12.000 | 16.000 | 288–383 |
| 5 | 16.000 | 20.000 | 384–479 |
| 6 | 20.000 | 24.000 | 480–575 |
| 🔁 | 24.000 | 0.000 | লুপ |

---

# 🎬 PART 2 — গল্প (এক লাইনে)

**Leo আয়নায় নিজেকে দেখে → প্রতিবিম্ব আলাদা কিছু করে → ক্যামেরা আয়নায় ঢুকে যায় → ভেতরে আবার একই রুম, একই Leo → লুপ।**

এটা **ড্রোস্টে ইফেক্ট** — ক্যামেরা যখন আয়নায় ঢোকে, দর্শক নতুন দৃশ্য দেখতে পায়, কিন্তু আসলে সেটা শুরুতে ফিরে গেছে। **এটাই সবচেয়ে hypnotic লুপ।**

---

# 🎬 PART 3 — শট-বাই-শট স্ক্রিপ্ট

## 🎬 SHOT 1 — ESTABLISH (0.000 – 4.000s)

**কম্পোজিশন:** মাঝখানে বড় আয়না, বাঁয়ে Leo, ডানে Lily।

**অ্যাকশন:**
- 0.0: Leo আয়নার দিকে হাত বাড়ায়
- 1.5: Lily পেছনে দাঁড়িয়ে হাসে
- 3.0: আয়নায় Leo-র প্রতিবিম্ব **একটু দেরিতে** নড়ে (0.2s delay — অলৌকিক ফিল)

**ক্যামেরা:** Static wide, ধীরে ২% zoom-in (0.0 → 4.0)

**অডিও:** 🎵 bar 1-2 (C-E-G-E মোটিফ) + 🔔 glass shimmer

**অন-স্ক্রিন টেক্সট:** `আয়নায় কী দেখছো? 👀`

> 💡 **অ্যাডভান্সড ডিটেইল:** প্রতিবিম্বের ০.২ সেকেন্ড দেরি — দর্শকের অবচেতন "কিছু একটা অদ্ভুত" টের পায়, কিন্তু ধরতে পারে না। এটাই লুপে বারবার দেখার কারণ।

---

## 🎬 SHOT 2 — REFLECTION BREAKS (4.000 – 8.000s)

**কম্পোজিশন:** আয়নার ক্লোজ-আপ (স্ক্রিনের ৭০%)।

**অ্যাকশন:**
- 4.0: প্রতিবিম্ব হাসে — কিন্তু Leo হাসে না (**pattern break!**)
- 5.0: প্রতিবিম্ব হাত নাড়ে → Leo অবাক হয়ে নিজের হাত দেখে
- 6.5: প্রতিবিম্ব **চোখ টিপে** (wink)

**ক্যামেরা:** Slow push-in (আয়নার দিকে ১০%)

**অডিও:** 🎵 bar 3-4 + ✨ reversed chime (উল্টো শব্দ — অস্বাভাবিক ফিল)

**টেক্সট:** `সে কী করছে?! 😱`

> 💡 **Rewatch Trigger:** প্রতিবিম্ব কি সত্যিই আলাদা কিছু করছে? — দ্বিতীয় বার দেখলে খেয়াল করবে।

---

## 🎬 SHOT 3 — THE TOUCH (8.000 – 12.000s)

**কম্পোজিশন:** দুই দিক থেকে হাত এগিয়ে আসে — আয়নার দুই পাশ।

**অ্যাকশন:**
- 8.0: Leo হাত বাড়ায়, প্রতিবিম্বও বাড়ায়
- 9.5: দুই আঙুল **আয়নার কাচে মিলে যায়** → 🌊 রিপল ইফেক্ট
- 10.5: কাচ **তরল হয়ে যায়** — হাত ঢুকে যায়
- 11.5: পুরো আয়না আলোয় ভরে যায়

**ক্যামেরা:** হাতের ক্লোজ-আপ → আয়নার ভেতরে zoom

**অডিও:** 🎵 bar 5-6 + 💧 water drop + 🎶 riser (উঠতি টোন)

**টেক্সট:** `ধরো আমার হাত! 🤝`

---

## 🎬 SHOT 4 — ENTER THE MIRROR (12.000 – 16.000s)

**কম্পোজিশন:** ক্যামেরা কাচ ভেদ করে ভেতরে ঢুকছে।

**অ্যাকশন:**
- 12.0: আলোর সুড়ঙ্গ (tunnel) — রংধনু আলোর রিং
- 13.5: রিংগুলো ঘুরছে (spiral motion)
- 15.0: দূরে একটা ছোট দৃশ্য দেখা যাচ্ছে — **একটা রুম**

**ক্যামেরা:** Constant-speed zoom-in (কোনো accel/decel নেই — লুপের জন্য জরুরি)

**অডিও:** 🎵 bar 7-8 + 🌌 whoosh + reversed reverb

**টেক্সট:** `ভেতরে কী আছে? 🌀`

> ⚠️ **গুরুত্বপূর্ণ:** এই শটের গতি **একদম সমান** হতে হবে। শুরু আর শেষে গতি বদলালে লুপে আটকে যাবে।

---

## 🎬 SHOT 5 — THE REVEAL (16.000 – 20.000s)

**কম্পোজিশন:** সুড়ঙ্গের শেষে — **আবার সেই রুম!**

**অ্যাকশন:**
- 16.0: ক্যামেরা বেরিয়ে আসে — একই রুম, একই আয়না
- 17.5: Leo আর Lily আয়নার সামনে দাঁড়িয়ে (SHOT 1-এর মতো!)
- 19.0: দুজনেই ক্যামেরার দিকে তাকিয়ে হাসে

**ক্যামেরা:** Zoom-out ধীরে থামে → **হুবহু SHOT 1-এর ফ্রেমে** ল্যান্ড করে

**অডিও:** 🎵 bar 9-10 + ✨ shimmer (SHOT 1-এর মতোই)

**টেক্সট:** `আবার এখানে?! 🤯`

> 🔥 **এখানেই লুপের জাদু:** দর্শক ভাবে "নতুন রুম", কিন্তু এটা SHOT 1। ক্যামেরা থামার সাথে সাথে লুপ।

---

## 🎬 SHOT 6 — CLOSE THE LOOP (20.000 – 24.000s)

**কম্পোজিশন:** SHOT 1-এর হুবহু কম্পোজিশন।

**অ্যাকশন:**
- 20.0: Leo আয়নার দিকে হাত বাড়ায় (SHOT 1-এর 0.0s-এর মতোই)
- 22.0: Lily পেছনে হাসে (SHOT 1-এর 1.5s-এর মতোই)
- 23.5: প্রতিবিম্ব আবার ০.২s দেরিতে নড়ে
- 24.0: 🔁 **লুপ** — দর্শক 0.0s-এ ফিরে যায়

**ক্যামেরা:** Static + ২% zoom-in (SHOT 1-এর মতো)

**অডিও:** 🎵 bar 11-12 — শেষ beat = প্রথম beat (হুবহু একই নোট)

**টেক্সট:** (কোনো টেক্সট নেই — লুপ পরিষ্কার)

---

# 🎨 PART 4 — পারালাক্স লেয়ার সিস্টেম (প্রো টেকনিক)

লুপকে "গভীর" দেখাতে ৩টা লেয়ার আলাদা গতিতে চলবে:

| লেয়ার | কী | গতি | লুপ দৈর্ঘ্য |
|---|---|---|---|
| **Background** | দেয়াল, জানালা, তাক | ০.৫x | ৪৮s (২ বার ভিডিওতে) |
| **Midground** | আয়না, টেবিল | ১.০x | ২৪s |
| **Foreground** | Leo, Lily, ধুলো কণা | ১.৫x | ১৬s |

**কীভাবে বানাবে:** AI-তে ৩টা আলাদা ক্লিপ বানিয়ে ffmpeg-এ overlay করো — প্রতিটার গতি `setpts` দিয়ে আলাদা করো। এতে চোখ বিভ্রান্ত হয়, আর লুপ টের পায় না।

```bash
# উদাহরণ: background ০.৫x গতিতে
ffmpeg -i bg.mp4 -filter_complex "[0:v]setpts=2.0*PTS[bg]" -map "[bg]" bg_slow.mp4
```

---

# 🎵 PART 5 — অডিও ডিজাইন (লুপ-পারফেক্ট)

## মিউজিক গ্রিড (120 BPM)
```
Bar 1-2  : মোটিফ (C-E-G-E)     — xylophone
Bar 3-4  : প্রতিবিম্ব ভাঙা     — reversed chime যোগ
Bar 5-6  : হাত মেলানো          — water drop + riser
Bar 7-8  : সুড়ঙ্গ              — whoosh + reverb swell
Bar 9-10 : আবার রুম            — motif ফিরে আসে
Bar 11-12: লুপ ক্লোজ           — bar 1-এর হুবহু কপি
```

## ⚠️ অডিওর ৩টা নিয়ম
1. **শেষ bar = প্রথম bar** (হুবহু, নোট-বাই-নোট)
2. **কোনো fade-out নেই** — শেষে ভলিউম কমলে লুপ ভাঙে
3. **Riser শেষ হবে beat-এ** — মাঝপথে নয়

## SFX টাইমলাইন
| সময় | শব্দ | নোট |
|---|---|---|
| 0.0 | 🔔 glass shimmer | শুরুর সিগনেচার |
| 3.0 | ✨ delayed reflection tick | প্রতিবিম্ব দেরি |
| 9.5 | 💧 water drop | হাত মেলে |
| 10.5 | 🌊 liquid glass | কাচ তরল |
| 12.0 | 🌀 tunnel whoosh | ঢোকা |
| 16.0 | ✨ shimmer (0.0-এর মতো) | ফেরা |
| 24.0 | 🔔 glass shimmer | 🔁 হুবহু 0.0 |

---

# 🤖 PART 6 — AI জেনারেশন: অ্যাডভান্সড প্রম্পট ইঞ্জিনিয়ারিং

## ধাপ ১ — Keyframe ফার্স্ট (সবচেয়ে গুরুত্বপূর্ণ)

```
Cute 3D Pixar-style orange tabby cat, blue polo shirt, standing in front of a
large ornate mirror in a cozy pastel kids room, neon-pastel lighting,
window with warm sunset light on the left, wooden shelf with toys on the right,
mirror perfectly centered, symmetrical composition, vertical 9:16,
cinematic depth of field, character reference sheet, high detail
```

> ⚠️ **সেভ করো এই ইমেজ।** এটাই SHOT 1 এবং SHOT 6-এর মূল ফ্রেম।

## ধাপ ২ — Image-to-Video (seed lock সহ)

| শট | প্রম্পট | কীwatch |
|---|---|---|
| **1** | `Camera slowly pushes in 2%, the cat raises hand toward mirror, kitten smiles behind, mirror reflection lags 0.2s behind, static composition, 4 seconds, 24fps` | গতি সমান |
| **2** | `Close up on mirror, the reflection smiles while the real cat does not, reflection waves, reflection winks, slight camera push in, 4s` | pattern break |
| **3** | `Two hands reach toward each other from both sides of the mirror, fingertips touch glass, water ripple effect, glass turns liquid, hand passes through, bright glow, 4s` | রিপল টাইমিং |
| **4** | `Camera flies through liquid mirror into a rainbow light tunnel, spiral rings rotating, constant speed zoom, distant room visible at the end, 4s` | **constant speed** |
| **5** | `Camera exits tunnel into the same cozy kids room, cat and kitten standing in front of mirror, they turn and smile at camera, camera settles, 4s` | SHOT 1-এ ল্যান্ড |
| **6** | `Same composition as first shot, cat raises hand toward mirror again, kitten smiles, reflection lags 0.2 seconds, static camera, 4s` | হুবহু 1 |

## ধাপ ৩ — সিড লক ও কনসিস্টেন্সি

| সমস্যা | সমাধান |
|---|---|
| চেহারা বদলায় | image-to-video + **same seed** (Runway: seed number লিখে রাখো) |
| আয়না অন্য রকম | প্রম্পটে "ornate mirror, same as reference" |
| আলো বদলায় | "warm sunset light from left window" — প্রতিবার একই বাক্য |
| গতি এলোমেলো | "constant speed", "no acceleration" |
| শেষ ফ্রেম মেলে না | শেষ শটে "end exactly on the first frame pose" |

## ধাপ ৪ — 16:9 ভার্সন
সব প্রম্পটে `vertical 9:16` → `horizontal 16:9` বদলাও। বাকি সব একই।

---

# 🛠️ PART 7 — পোস্ট-প্রোডাকশন কমান্ড

## ক্লিপ জোড়া লাগানো (frame-accurate)
```bash
# clips.txt
file 'shot1.mp4'
file 'shot2.mp4'
file 'shot3.mp4'
file 'shot4.mp4'
file 'shot5.mp4'
file 'shot6.mp4'

ffmpeg -f concat -safe 0 -i clips.txt -c copy joined.mp4
```

## লুপ ভেরিফাই (কতটা seamless?)
```bash
python3 verify_loop.py joined.mp4
```
→ ০.৯৭+ SSIM = নিখুঁত লুপ ✅

## লুপ রিপিট (watch time ×N)
```bash
python3 make_loop.py joined.mp4 --repeat 5
```

---

# 🎯 PART 8 — কেন এই লুপ অ্যাডিক্টিভ (মনস্তত্ত্ব)

| ট্রিগার | কীভাবে প্রয়োগ | মস্তিষ্কে কী হয় |
|---|---|---|
| **Zeigarnik Effect** | ৩s-এ অসম্পূর্ণ প্রশ্ন ("আয়নায় কী দেখছো?") | মস্তিষ্ক উত্তর খোঁজে — থামতে পারে না |
| **Delayed Mirror** | প্রতিবিম্ব ০.২s দেরি | অবচেতন অস্বস্তি → বারবার দেখে |
| **Pattern Break** | প্রতিবিম্ব আলাদা হাসে | প্রত্যাশা ভাঙে → মনোযোগ ফেরে |
| **Droste Effect** | আয়নার ভেতরে আয়না | অসীমতার অনুভূতি — hypnotic |
| **Beat Sync** | সব কাট beat-এ | মস্তিষ্ক ছন্দে দোলে — নেশার মতো |
| **Loop Illusion** | শেষ = শুরু | "আর একবার" — নিজেও জানে না কেন |

> 🧠 **সবচেয়ে বড় রহস্য:** দর্শক জানে ভিডিও শেষ হয়েছে, কিন্তু **চোখ মানতে চায় না**।
> ফলে সে নিজে থেকে আরেকবার দেখে — অ্যালগরিদম এটাকে "high rewatch" গোনে → বুস্ট।

---

# 📊 PART 9 — A/B টেস্ট প্ল্যান

| ভ্যারিয়েন্ট | কী বদলাবে | কী মাপবে |
|---|---|---|
| **A** | মূল (delay 0.2s) | baseline |
| **B** | delay 0.5s (আরও অদ্ভুত) | rewatch rate |
| **C** | প্রতিবিম্ব wink বাদ | retention |
| **D** | সুড়ঙ্গ ২s (আরও দীর্ঘ) | watch time |
| **E** | ২৪s → ১৮s (কাটছাঁট) | completion rate |

**মাপার সূত্র:**
```
Rewatch Rate = Views / Unique Viewers
Completion   = Average View Duration / Video Length
```
> Rewatch Rate **১.৫+** হলে ভিডিও ভাইরাল হওয়ার পথে। 🚀

---

# ✅ PART 10 — প্রো চেকলিস্ট (২০ পয়েন্ট)

**ডিজাইন**
- [ ] শেষ ফ্রেম = প্রথম ফ্রেম (pixel-perfect)
- [ ] আলোর দিক একই (বাঁ দিকের জানালা)
- [ ] ক্যামেরার উচ্চতা একই
- [ ] ক্যারেক্টারের পোজ একই

**টাইমিং**
- [ ] ৫৭৬ ফ্রেম @ 24fps
- [ ] সব কাট beat-এ (প্রতি ১২ ফ্রেম)
- [ ] কোনো শটে accel/decel নেই

**অডিও**
- [ ] শেষ bar = প্রথম bar
- [ ] fade-out নেই
- [ ] SFX 0.0s = SFX 24.0s
- [ ] riser beat-এ শেষ

**ভিজ্যুয়াল**
- [ ] ড্রোস্টে জুমের গতি সমান
- [ ] প্রতিবিম্বের ০.২s delay আছে
- [ ] pattern break আছে (প্রতিবিম্ব আলাদা হাসে)
- [ ] পারালাক্স লেয়ার আলাদা গতিতে

**টেকনিক্যাল**
- [ ] `verify_loop.py` দিয়ে SSIM ০.৯৭+
- [ ] `make_loop.py` দিয়ে রিপিট
- [ ] ৩ বার প্লে করে ঝাঁকুনি চেক
- [ ] মোবাইলে (ছোট স্ক্রিনে) টেস্ট
