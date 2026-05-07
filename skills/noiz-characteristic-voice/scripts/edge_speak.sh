#!/usr/bin/env bash
# Edge TTS wrapper for characteristic-voice skill
set -euo pipefail

ACTIVATE_VENV="/root/.openclaw/workspace/freqtrade-env/bin/activate"

usage() {
  cat <<'EOF'
Usage:
  edge_speak.sh [--preset MODE] -t "text" -o output.mp3

Presets:
  goodnight  gentle, warm (slower)
  morning    warm, cheerful  
  comfort    soft, unhurried
  celebrate  excited, faster
  chat       relaxed, natural
EOF
  exit 0
}

[[ "$1" == "-h" ]] && usage

VOICE="zh-CN-XiaoxiaoNeural"
RATE="+0%"
TEXT=""
OUTPUT=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    -t) TEXT="$2"; shift 2 ;;
    -o) OUTPUT="$2"; shift 2 ;;
    --preset)
      case "$2" in
        goodnight) RATE="-15%" ;;
        morning)   RATE="+0%" ;;
        comfort)   RATE="-20%" ;;
        celebrate) VOICE="zh-CN-XiaoyiNeural"; RATE="+15%" ;;
        chat)      RATE="+0%" ;;
      esac
      shift 2 ;;
    --voice) VOICE="$2"; shift 2 ;;
    --rate) RATE="$2"; shift 2 ;;
    *) shift ;;
  esac
done

[[ -z "$TEXT" ]] && echo "Error: -t required" && exit 1
[[ -z "$OUTPUT" ]] && echo "Error: -o required" && exit 1

. "$ACTIVATE_VENV"
edge-tts --voice "$VOICE" --rate="$RATE" --text "$TEXT" --write-media "$OUTPUT"
echo "✓ $OUTPUT"
