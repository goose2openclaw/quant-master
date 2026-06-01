#!/bin/bash
# QuantMaster APK Build Script
# Requires: npx @capacitor/cli, npx @capacitor/android

echo "==================================="
echo "QuantMaster APK Builder"
echo "==================================="

# Check Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found"
    exit 1
fi

# Create React PWA project
echo "📱 Creating React PWA project..."
npx create-react-app quantmaster-app --template cra-template-pwa

cd quantmaster-app

# Copy WebUI files
cp -r ../ui/* src/

# Install Capacitor
echo "⚡ Installing Capacitor..."
npm install @capacitor/core @capacitor/cli @capacitor/android

# Initialize Capacitor
npx cap init QuantMaster com.quantmaster.app --web-dir=build

# Add Android platform
echo "🤖 Adding Android platform..."
npx cap add android

# Build web app
echo "🔨 Building web app..."
npm run build

# Sync to Android
npx cap sync android

# Build APK
echo "📦 Building APK..."
cd android
./gradlew assembleDebug

# Find APK
APK=$(find . -name "*.apk" -type f | head -1)
if [ -n "$APK" ]; then
    echo "✅ APK built: $APK"
    cp "$APK" ../quantmaster.apk
    echo "📍 Saved to: ../quantmaster.apk"
else
    echo "❌ APK build failed"
fi

echo "==================================="
echo "Build complete!"
echo "==================================="
