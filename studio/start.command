#!/bin/zsh
# MithuStudio — ডাবল-ক্লিক করে চালাও 🎬
cd "$(dirname "$0")/.." || exit 1

PORT=8765
# আগে থেকে চললে বন্ধ করা
pkill -f "studio/server.py" >/dev/null 2>&1
sleep 0.5

python3 studio/server.py "$PORT" &
SERVER_PID=$!

sleep 1.5
open "http://127.0.0.1:$PORT"

echo ""
echo "🎬 MithuStudio চালু আছে — এই উইন্ডোটা বন্ধ করলে স্টুডিওও বন্ধ হবে।"
wait $SERVER_PID
