#!/usr/bin/env python3
"""
AirTouch macOS App & DMG Packaging Script
- Creates AppIcon.iconset from source 1024x1024 PNG
- Uses iconutil to generate AirTouch.icns
- Runs PyInstaller with custom Info.plist (Camera permissions, etc.)
- Bundles hand_landmarker.task
- Packages into AirTouch.dmg with Applications shortcut
"""

import os
import sys
import shutil
import subprocess
from PIL import Image

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def create_icns(source_png: str, output_icns: str):
    iconset_dir = os.path.join(BASE_DIR, "AppIcon.iconset")
    if os.path.exists(iconset_dir):
        shutil.rmtree(iconset_dir)
    os.makedirs(iconset_dir, exist_ok=True)

    img = Image.open(source_png).convert("RGBA")

    sizes = [
        ("icon_16x16.png", (16, 16)),
        ("icon_16x16@2x.png", (32, 32)),
        ("icon_32x32.png", (32, 32)),
        ("icon_32x32@2x.png", (64, 64)),
        ("icon_128x128.png", (128, 128)),
        ("icon_128x128@2x.png", (256, 256)),
        ("icon_256x256.png", (256, 256)),
        ("icon_256x256@2x.png", (512, 512)),
        ("icon_512x512.png", (512, 512)),
        ("icon_512x512@2x.png", (1024, 1024)),
    ]

    for filename, size in sizes:
        resized = img.resize(size, Image.Resampling.LANCZOS)
        resized.save(os.path.join(iconset_dir, filename), "PNG")

    subprocess.run(["iconutil", "-c", "icns", iconset_dir, "-o", output_icns], check=True)
    shutil.rmtree(iconset_dir)
    print(f"✅ Generated {output_icns}")

def create_plist(plist_path: str):
    plist_content = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>AirTouch</string>
    <key>CFBundleDisplayName</key>
    <string>AirTouch</string>
    <key>CFBundleIdentifier</key>
    <string>com.oarabile.airtouch</string>
    <key>CFBundleVersion</key>
    <string>1.0.0</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0.0</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleIconFile</key>
    <string>AirTouch.icns</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>NSCameraUsageDescription</key>
    <string>AirTouch uses your camera for contactless hand gesture tracking and cursor control. Video stays 100% on-device.</string>
    <key>NSAppleEventsUsageDescription</key>
    <string>AirTouch requires accessibility control to dispatch native cursor clicks and media keys.</string>
</dict>
</plist>
"""
    with open(plist_path, "w") as f:
        f.write(plist_content)
    print(f"✅ Created Info.plist at {plist_path}")

def build_dmg():
    # Find source icon
    source_icon = os.path.join(BASE_DIR, "icon_1024.png")
    if not os.path.exists(source_icon):
        # Check subagent brain directories if saved there
        brain_dirs = [d for d in os.listdir(os.path.expanduser("~/.gemini/antigravity/brain"))]
        for b in brain_dirs:
            candidate = os.path.expanduser(f"~/.gemini/antigravity/brain/{b}/icon_1024.png")
            if os.path.exists(candidate):
                source_icon = candidate
                break

    icns_path = os.path.join(BASE_DIR, "AirTouch.icns")
    if os.path.exists(source_icon):
        create_icns(source_icon, icns_path)

    plist_path = os.path.join(BASE_DIR, "Info.plist")
    create_plist(plist_path)

    # Clean build dirs
    for d in ["build", "dist"]:
        if os.path.exists(d):
            shutil.rmtree(d)

    # PyInstaller command
    pyinstaller_bin = os.path.join(BASE_DIR, ".venv", "bin", "pyinstaller")
    cmd = [
        pyinstaller_bin,
        "--noconfirm",
        "--windowed",
        "--name", "AirTouch",
        "--collect-all", "mediapipe",
        "--add-data", f"{os.path.join(BASE_DIR, 'hand_landmarker.task')}:.",
        "--osx-bundle-identifier", "com.oarabile.airtouch",
    ]
    if os.path.exists(icns_path):
        cmd.extend(["--icon", icns_path])

    # Remove empty args
    cmd = [c for c in cmd if c]
    cmd.append(os.path.join(BASE_DIR, "gesture_mouse.py"))

    print(f"🚀 Running PyInstaller...")
    subprocess.run(cmd, check=True)

    app_path = os.path.join(BASE_DIR, "dist", "AirTouch.app")
    if not os.path.exists(app_path):
        print("❌ AirTouch.app was not created!")
        sys.exit(1)

    # Copy Info.plist into AirTouch.app/Contents/Info.plist
    contents_plist = os.path.join(app_path, "Contents", "Info.plist")
    shutil.copy2(plist_path, contents_plist)

    # Copy icns into AirTouch.app/Contents/Resources/
    if os.path.exists(icns_path):
        res_dir = os.path.join(app_path, "Contents", "Resources")
        os.makedirs(res_dir, exist_ok=True)
        shutil.copy2(icns_path, os.path.join(res_dir, "AirTouch.icns"))

    # Re-sign the app bundle so the modified Info.plist does not invalidate the signature
    print("🔏 Re-signing AirTouch.app with ad-hoc signature...")
    subprocess.run(["codesign", "--force", "--deep", "--sign", "-", app_path], check=True)

    print("✅ AirTouch.app created, patched, and signed successfully!")

    # Prepare DMG folder
    dmg_staging = os.path.join(BASE_DIR, "dmg_staging")
    if os.path.exists(dmg_staging):
        shutil.rmtree(dmg_staging)
    os.makedirs(dmg_staging, exist_ok=True)

    # Copy .app to staging
    shutil.copytree(app_path, os.path.join(dmg_staging, "AirTouch.app"), symlinks=True)

    # Create /Applications symlink
    os.symlink("/Applications", os.path.join(dmg_staging, "Applications"))

    # Create DMG
    dmg_output = os.path.join(BASE_DIR, "AirTouch.dmg")
    if os.path.exists(dmg_output):
        os.remove(dmg_output)

    print(f"📦 Packaging DMG using hdiutil...")
    subprocess.run([
        "hdiutil", "create",
        "-volname", "AirTouch",
        "-srcfolder", dmg_staging,
        "-ov",
        "-format", "UDZO",
        dmg_output
    ], check=True)

    shutil.rmtree(dmg_staging)
    print(f"🎉 Successfully created {dmg_output}!")

if __name__ == "__main__":
    build_dmg()

