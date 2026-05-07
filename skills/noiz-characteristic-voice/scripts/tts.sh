#!/usr/bin/env bash
# Unified TTS wrapper - supports Edge TTS (default, no API needed)
# Usage: tts.sh --preset goodnight -t "text" -o output.mp3
set -euo pipefail

ACTIVATE_VENV="/root/.openclaw/workspace/freqtrade-env/bin/activate"

usage() {
  cat <<'EOF'
TTS Wrapper (Edge TTS - no API key needed)

Usage: tts.sh [options]

Presets:
  goodnight  gentle, warm, slower
  morning    warm, cheerful
  comfort    soft, unhurried
  celebrate  excited, faster
  chat       relaxed, natural

Options:
  -t TEXT     Text to speak
  -o FILE     Output file
  --voice     Custom voice (default: zh-CN-XiaoxiaoNeural)
  --speed     Speed adjustment (e.g., 0.8, 1.0, 1.2)
EOF
  exit 0
}

[[ "$1" == "-h" ]] && usage

VOICE="zh-CN-XiaoxiaoNeural"
SPEED="1.0"
TEXT=""
OUTPUT=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    -t) TEXT="$2"; shift 2 ;;
    -o) OUTPUT="$2"; shift 2 ;;
    --preset)
      case "$2" in
        goodnight) SPEED="0.85" ;;
        morning)   SPEED="1.0" ;;
        comfort)   SPEED="0.8" ;;
        celebrate) VOICE="zh-CN-XiaoyiNeural"; SPEED="1.1" ;;
        chat)      SPEED="1.0" ;;
      esac
      shift 2 ;;
    --voice) VOICE="$2"; shift 2 ;;
    --speed) SPEED="$2"; shift 2 ;;
    *) shift ;;
  esac
done

[[ -z "$TEXT" ]] && echo "Error: -t required" && exit 1
[[ -z "$OUTPUT" ]] && echo "Error: -o required" && exit 1

. "$ACTIVATE_VENV"

# Convert speed to edge-tts rate format
RATE=$(python3 -c "rate = float('$SPEED'); print(f'{\"+\" if rate >= 1 else \"-\"}{int(abs(rate - 1) * 100)}%')")

edge-tts --voice "$VOICE" --rate="$RATE" --text "$TEXT" --write-media "$OUTPUT" 2>/dev/null
echo "✓ $OUTPUT"
