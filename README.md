# AirTouch 🖐️✨

Control your entire Mac cursor, click, drag, scroll, slide spaces, adjust brightness, and change volume using camera hand gestures — completely touch-free! Built with **Python**, **OpenCV**, **Google MediaPipe**, and native macOS **Quartz / AppKit / PyAutoGUI**.

---

## 🚀 Installation & Quick Start

### 📦 Option 1: Standalone macOS App (.dmg)
Download the standalone disk image for Apple Silicon & Intel Macs:

[**⬇️ Download AirTouch.dmg (v1.0.0 Beta)**](https://github.com/Oarabile-Seboka/airtouch/releases/download/v1.0.0-beta/AirTouch.dmg)

1. Open `AirTouch.dmg` and drag **AirTouch** into your `/Applications` folder.
2. Launch AirTouch from Applications.
3. *macOS Gatekeeper notice*: On first launch, macOS may prompt that the developer cannot be verified. Simply **Right-Click (or Control-Click) AirTouch.app > Open**, or go to **System Settings > Privacy & Security** and click **Open Anyway**.  
   *(Or run `xattr -cr /Applications/AirTouch.app` in Terminal).*
4. Grant **Camera** and **Accessibility** permissions when prompted.

---

### 💻 Option 2: Run from Source (Terminal)

```bash
# 1. Clone the repository
git clone https://github.com/Oarabile-Seboka/airtouch.git
cd airtouch

# 2. Run AirTouch (automatically sets up .venv and installs dependencies)
chmod +x run.sh
./run.sh
```

---

## ⚙️ macOS Permissions

AirTouch needs two macOS permissions to control your cursor and read your camera:

1. **Camera**: **System Settings > Privacy & Security > Camera**  
   → Enable toggle for **Terminal** (or iTerm / your terminal emulator).
2. **Accessibility**: **System Settings > Privacy & Security > Accessibility**  
   → Enable toggle for **Terminal** (or your Python runtime) to allow cursor clicks and keyboard shortcuts.

---

## ✋ Complete Gestures Cheat Sheet

| Fingers / Pose | Action | Details |
| :---: | :--- | :--- |
| **👉 1 Finger (Index)** | **Move Cursor** | Point and glide across screen with EMA smoothing |
| **🔒 Thumb Near Index** | **Anchor Lock** | Freezes cursor on target so your aim never slips |
| **🤏 Thumb + Index (Tap)** | **Instant Left Click** | Millisecond click registration on release |
| **✊ Pinch & Hold (>0.28s)** | **Real Drag** | Move windows, drag files, select text |
| **👌 Thumb + Middle** | **Right Click** | Secondary click |
| **✌️ 2 Fingers (Index+Middle)** | **Fluid Scroll** | Move up/down to scroll with dynamic acceleration |
| **🖐️ 3 Fingers (Index+Mid+Ring)** | **Slide Spaces / Mission Control** | Swipe Left/Right = Slide Desktops, Swipe Up = Mission Control |
| **☀️ 4 Fingers Up (Hold ~0.45s)** | **Brightness Control** | Hold steadily to engage, then move hand Up / Down |
| **🤘 Rock On (Hold ~0.35s)** | **Volume Control** | Hold steadily to engage, then move hand Up / Down |
| **✊ Closed Fist** | **Quick Pause** | Temporarily halts cursor movement |
| **👍 Thumbs Up (Hold ~0.5s)** | **Toggle SUSPEND / RESUME** | Freezes all tracking completely until toggled back on |

---

## ⌨️ In-App Hotkeys

While the camera preview window is focused:
* **`q`** : Quit AirTouch
* **`h`** : Toggle HUD camera preview window on/off

---

## 👨‍💻 Author

Designed & developed by **[Oarabile Seboka](https://www.seboka.co.za/)**.


