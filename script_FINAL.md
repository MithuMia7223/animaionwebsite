# 🎁 FINAL LOOP SCRIPT — "ম্যাজিক বক্স" (The Magic Box)

**দৈর্ঘ্য:** ২০ সেকেন্ড · **ফরম্যাট:** 9:16 Vertical · **বয়স:** ২–৫ বছর
**টাইপ:** Seamless Loop — শেষ ফ্রেম = প্রথম ফ্রেম 🔁

---

## 🎯 এক লাইনে গল্প

> **বক্স বন্ধ → খোলে → বল বের হয় → খেলা → বল ফিরে যায় → বক্স বন্ধ → আবার শুরু**

এটা **চক্রাকার গল্প** — তাই লুপ করলে মনে হয় গল্প চলছেই।

---

## 📊 ৫টা শট (২০ সেকেন্ড)

| # | সময় | কী হবে | অন-স্ক্রিন টেক্সট |
|---|---|---|---|
| **১** | 0–3s | মেঝেতে **বন্ধ ম্যাজিক বক্স**। Leo হেঁটে এসে বক্সের পাশে দাঁড়ায়, ক্যামেরার দিকে তাকিয়ে হাসে। | `কী আছে ভেতরে? 👀` |
| **২** | 3–7s | Leo ঢাকনা খোলে → **রংধনু আলো** ছড়ায় → **বড় লাল বল** লাফিয়ে বের হয় | `টিং! ✨` |
| **৩** | 7–13s | Leo বল বাউন্স করে (টপ টপ টপ)। একবার বল মাথায় পড়ে, হোঁচট খায় 😂 | `উফ! 😅` |
| **৪** | 13–17s | বলটা হঠাৎ লাফ দিয়ে **বক্সে ফিরে যায়**। Leo অবাক 😮 | `বলটা গেল! 😱` |
| **৫** | 17–20s | বক্স নিজে থেকে **বন্ধ হয়ে যায়**। Leo আবার ক্যামেরার দিকে তাকিয়ে হাসে — **হুবহু শট ১-এর মতো**। | (কোনো টেক্সট না) |
| 🔁 | 20s | লুপ! | — |

---

## 🎵 অডিও (সহজ)

| সময় | শব্দ |
|---|---|
| 0s | 🎵 হালকা xylophone শুরু (৫ নোট) |
| 3s | ✨ "টিং!" + ঢাকনা খোলার শব্দ |
| 7–13s | 🎈 টপ-টপ-টপ (বল বাউন্স) + 😂 হাসি |
| 13s | 💨 "শুউউ!" (বল উড়ে যায়) |
| 17s | 🤫 ঢাকনা বন্ধের "ঠক" |
| 20s | 🎵 শুরুর ৫ নোট (হুবহু একই) |

> ⚠️ শেষের ৫ নোট = শুরুর ৫ নোট। এটা বাদ দিলে লুপে টের পাওয়া যাবে।

---

## 🤖 AI প্রম্পট (৫টা, কপি-রেডি)

**১. প্রথম ফ্রেম (এটা আগে বানাও, সেভ করো):**
```
Cute 3D Pixar-style orange tabby cat in blue polo shirt, standing next to a
closed golden magic box on a wooden floor, bright pastel kids room, big green
eyes, happy smile, soft daylight, vertical 9:16, high detail
```

**২. বক্স খোলা:**
```
Image to video: the cat opens the magic box lid, rainbow light bursts out,
a big red ball pops up from inside, sparkles fly, bright kids room, 4 seconds
```

**৩. বল খেলা:**
```
Image to video: the cat bounces a big red ball on the floor repeatedly,
happy laughing expression, ball bounces off his head once, he stumbles
comically, bright kids room, 6 seconds
```

**৪. বল ফিরে যাওয়া:**
```
Image to video: the big red ball suddenly bounces high and falls back into
the magic box, the cat looks shocked with wide eyes, mouth open, 4 seconds
```

**৫. বক্স বন্ধ (লুপ ক্লোজ):**
```
Image to video: the golden magic box lid closes by itself, the cat turns to
camera and smiles happily, exact same pose as the first frame, static camera,
soft daylight, 3 seconds
```

---

## ✅ লুপ চেক (৩টা জিনিস)

1. শট ৫-এর শেষ পোজ = শট ১-এর পোজ (হুবহু)
2. শেষের ৫ নোট = শুরুর ৫ নোট
3. শেষে কোনো fade-out নেই

তারপর চালাও:
```bash
python3 verify_loop.py video.mp4      # লুপ মসৃণ কিনা মাপে
python3 make_loop.py video.mp4 --repeat 5   # ৫ বার লুপ (watch time বাড়ায়)
```

---

## 💡 কেন এটা কাজ করবে

- **চক্রাকার গল্প** — শেষ = শুরু, তাই লুপে মনে হয় গল্প চলছে
- **কমেডি** — মাথায় বল পড়া, হোঁচট (প্রতিবার হাসি)
- **অবাক মোমেন্ট** — বল নিজে থেকে বক্সে ফিরে যায়
- **২০ সেকেন্ড** — ছোট, তাই বারবার দেখা সহজ
