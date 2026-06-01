# QuantMaster APK Build Guide

## Option 1: PWA (Progressive Web App) - Recommended

PWA works like an APK and can be installed on Android home screen.

1. Open http://localhost:8088 on Android Chrome
2. Tap Menu → "Add to Home Screen"
3. Done! Works offline

## Option 2: Capacitor APK Build

### Prerequisites
```bash
# Node.js 18+
node --version

# Android SDK (for APK build)
echo $ANDROID_HOME
```

### Build Steps
```bash
cd /home/goose/.openclaw/workspace/quant_master/apk
./build_apk.sh
```

This will create `quantmaster.apk` in the project root.

## Option 3: Localtunnel for Mobile Access

Expose WebUI to internet for mobile testing:
```bash
npx localtunnel --port 8088
```

## Files
- `manifest.json` - PWA manifest for installability
- `build_apk.sh` - Capacitor APK build script
