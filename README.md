# Mac Hand Gesture Controller 🖐️🖱️

Control your entire Mac cursor, click, drag, scroll, slide spaces, adjust brightness, and change volume using camera hand gestures! Built with **Python**, **OpenCV**, **Google MediaPipe**, and native macOS **Quartz / AppKit / PyAutoGUI**.

---

## 🚀 Quick Start

```bash
cd ~/Personal-Dev-Projects/mac-gesture-mouse
./run.sh
```

---

## ✋ Complete Gestures Cheat Sheet

| Fingers / Pose | Action | Details |
| :---: | :--- | :--- |
| **👉 1 Finger (Index)** | **Move Cursor** | Point and glide across screen with EMA smoothing |
| **🔒 Thumb Near Index** | **Anchor Lock** | Freezes cursor on target so your aim never slips |
| **🤏 Thumb + Index (Tap)** | **Instant Left Click** | Millisecond click registration on release |
| **✊ Pinch & Hold (>0.28s)** | **Real Drag** | Move windows, drag files, select text |
| **👌 Thumb + Middle** | **Right Click** | Secondary click |
| **✌️ 2 Fingers (Index+Middle)** | **Fluid Scroll** | Move up/down to scroll (dynamic acceleration) |
| **🖐️ 3 Fingers (Index+Mid+Ring)** | **Slide Spaces / Mission Control** | Swipe Left/Right = Slide Desktops, Swipe Up = Mission Control |
| **☀️ 4 Fingers Up (Hold ~0.45s)** | **Brightness Control** | Hold steadily to engage, then move hand Up / Down |
| **🤘 Rock On (Hold ~0.35s)** | **Volume Control** | Hold steadily to engage, then move hand Up / Down |
| **✊ Closed Fist** | **Quick Pause** | Temporarily halts cursor movement |
| **👍 Thumbs Up (Hold ~0.5s)** | **Toggle SUSPEND / RESUME** | Freezes all tracking completely until toggled back on |

---

## ⌨️ Hotkeys

In the camera preview window:
* **`q`** : Quit the application
* **`h`** : Toggle HUD camera window on/off

---

## ⚙️ macOS Permissions

* **Camera**: **System Settings > Privacy & Security > Camera** (toggle Terminal ON).
* **Accessibility**: **System Settings > Privacy & Security > Accessibility** (toggle Terminal ON).
