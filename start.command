#!/bin/zsh
# MithuStudio — ডাবল-ক্লিক করে চালাও 🎬
cd "$(dirname "$0")" || exit 1

PORT=8765
APP="$PWD/app/server.py"

# শুধু এই প্রজেক্টের সার্ভার বন্ধ করি — পুরো সিস্টেমে প্যাটার্ন মেলানো নয়
pkill -f "$APP" >/dev/null 2>&1
# পুরনোভাবে (রিলেটিভ পাথে) চালু হয়ে থাকলে সেটাও
pkill -f "Python app/server.py $PORT" >/dev/null 2>&1
sleep 0.6

python3 "$APP" "$PORT" &
SERVER_PID=$!

# সার্ভার সত্যিই উঠা পর্যন্ত অপেক্ষা, তারপর ব্রাউজার — নইলে এরর পেজ দেখায়
ready=0
for i in {1..40}; do
  if ! kill -0 $SERVER_PID 2>/dev/null; then break; fi   # সার্ভার মরে গেছে (পোর্ট ব্যস্ত ইত্যাদি)
  if curl -s -o /dev/null --max-time 1 "http://127.0.0.1:$PORT/"; then ready=1; break; fi
  sleep 0.25
done

if [ $ready -eq 1 ]; then
  open "http://127.0.0.1:$PORT"
else
  echo "⚠️ সার্ভার চালু হতে পারছে না — নিচের এররটা দেখো।"
fi

echo ""
echo "🎬 MithuStudio চালু আছে।"
echo "   এই উইন্ডোটা বন্ধ করলে স্টুডিওও বন্ধ হবে।"
wait $SERVER_PID
