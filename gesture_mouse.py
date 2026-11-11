#!/usr/bin/env python3
"""
Mac Hand Gesture Controller (v11 - Robust Latch & Bugfix)
Features:
- Fixed NameError: 'is_locked' -> 'is_anchored'
- Single-action latch for 👍 Thumbs Up (prevents infinite rapid toggle flip-flops)
- ☀️ Brightness Engagement Gate: Must hold 4 fingers for ~0.45s before adjustment begins
- 🔊 Volume Engagement Gate: Must hold 🤘 for ~0.35s before adjustment begins
- 🖐️ 3-Finger Swipe: Desktops / Spaces & Mission Control
- ✌️ 2-Finger Fluid Smooth Scroll: Sub-line accumulator with dynamic acceleration
- 👉 1-Finger Point & Click: Instant click, native drag, Anchor Lock
- 👍 Thumbs Up (Hold ~0.5s): Toggle SUSPEND / RESUME
"""

import math
import os
import sys
import time
import urllib.request
import threading
import subprocess
import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import pyautogui

# Quartz / AppKit for native macOS events and system media keys
try:
    import Quartz
    import Quartz.CoreGraphics as CG
    from AppKit import NSEvent, NSSystemDefined
    USE_QUARTZ = True
except ImportError:
    USE_QUARTZ = False

# Screen Dimensions
SCREEN_W, SCREEN_H = pyautogui.size()
pyautogui.PAUSE = 0.001
pyautogui.FAILSAFE = True

# Camera & Interactive Boundaries
CAM_WIDTH, CAM_HEIGHT = 640, 480
FRAME_MARGIN_X = 0.18
FRAME_MARGIN_Y = 0.20

# Smoothing & Sensitivities
SMOOTHING_ALPHA = 0.40
JITTER_THRESHOLD = 2.0

# Scroll Configuration
SCROLL_SENSITIVITY = 110.0
SCROLL_INVERT = False

# Volume & Brightness Engagement & Sensitivities
BRIGHTNESS_ENGAGE_TIME = 0.45  # Must hold 4 fingers for 0.45s before brightness adjusts
VOLUME_ENGAGE_TIME = 0.35      # Must hold 🤘 for 0.35s before volume adjusts
MEDIA_GESTURE_SENSITIVITY = 22.0

# 3-Finger Swipe Configuration (Desktops & Mission Control)
SWIPE_DIST_THRESHOLD = 0.08
SWIPE_COOLDOWN = 0.70

# Pinch & Anchor Settings
PINCH_PREPARE_DIST = 0.082
PINCH_CLICK_DIST = 0.058
PINCH_RELEASE_DIST = 0.075
DRAG_THRESHOLD_TIME = 0.28
RELEASE_COOLDOWN = 0.15
PINCH_RIGHT_DIST = 0.058

# Thumbs Up Toggle Settings
THUMBS_UP_HOLD_TIME = 0.55

if getattr(sys, 'frozen', False):
    BASE_DIR = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MODEL_FILE = os.path.join(BASE_DIR, "hand_landmarker.task")
MODEL_URL = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"

HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),        # Thumb
    (0, 5), (5, 6), (6, 7), (7, 8),        # Index
    (5, 9), (9, 10), (10, 11), (11, 12),   # Middle
    (9, 13), (13, 14), (14, 15), (15, 16), # Ring
    (13, 17), (17, 18), (18, 19), (19, 20),# Pinky
    (0, 17)                                # Palm Base
]


def ensure_model_file():
    if not os.path.exists(MODEL_FILE):
        print("⏳ Downloading MediaPipe HandLandmarker model (~7.5MB)...")
        urllib.request.urlretrieve(MODEL_URL, MODEL_FILE)
        print("✅ Model downloaded successfully.")


def mac_move_mouse(x: float, y: float):
    if USE_QUARTZ:
        try:
            point = CG.CGPoint(x, y)
            event = CG.CGEventCreateMouseEvent(None, CG.kCGEventMouseMoved, point, CG.kCGMouseButtonLeft)
            CG.CGEventPost(CG.kCGHIDEventTap, event)
            return
        except Exception:
            pass
    pyautogui.moveTo(x, y)


def mac_mouse_down(x: float, y: float):
    if USE_QUARTZ:
        try:
            point = CG.CGPoint(x, y)
            event = CG.CGEventCreateMouseEvent(None, CG.kCGEventLeftMouseDown, point, CG.kCGMouseButtonLeft)
            CG.CGEventPost(CG.kCGHIDEventTap, event)
            return
        except Exception:
            pass
    pyautogui.mouseDown(x, y)


def mac_mouse_up(x: float, y: float):
    if USE_QUARTZ:
        try:
            point = CG.CGPoint(x, y)
            event = CG.CGEventCreateMouseEvent(None, CG.kCGEventLeftMouseUp, point, CG.kCGMouseButtonLeft)
            CG.CGEventPost(CG.kCGHIDEventTap, event)
            return
        except Exception:
            pass
    pyautogui.mouseUp(x, y)


def mac_mouse_drag(x: float, y: float):
    if USE_QUARTZ:
        try:
            point = CG.CGPoint(x, y)
            event = CG.CGEventCreateMouseEvent(None, CG.kCGEventLeftMouseDragged, point, CG.kCGMouseButtonLeft)
            CG.CGEventPost(CG.kCGHIDEventTap, event)
            return
        except Exception:
            pass
    pyautogui.moveTo(x, y)


def mac_right_click(x: float, y: float):
    if USE_QUARTZ:
        try:
            point = CG.CGPoint(x, y)
            down = CG.CGEventCreateMouseEvent(None, CG.kCGEventRightMouseDown, point, CG.kCGMouseButtonRight)
            up = CG.CGEventCreateMouseEvent(None, CG.kCGEventRightMouseUp, point, CG.kCGMouseButtonRight)
            CG.CGEventPost(CG.kCGHIDEventTap, down)
            CG.CGEventPost(CG.kCGHIDEventTap, up)
            return
        except Exception:
            pass
    pyautogui.rightClick(x, y)


def mac_scroll_lines(lines: int):
    if USE_QUARTZ:
        try:
            event = CG.CGEventCreateScrollWheelEvent(None, CG.kCGScrollEventUnitLine, 1, int(lines))
            CG.CGEventPost(CG.kCGHIDEventTap, event)
            return
        except Exception:
            pass
    pyautogui.scroll(lines * 8)


def send_system_media_key(key_code: int, repeat: int = 1):
    for _ in range(repeat):
        if USE_QUARTZ:
            try:
                for down in (True, False):
                    flags = 0xa00 if down else 0xb00
                    data1 = (key_code << 16) | ((0xa if down else 0xb) << 8)
                    ev = NSEvent.otherEventWithType_location_modifierFlags_timestamp_windowNumber_context_subtype_data1_data2_(
                        NSSystemDefined, (0, 0), flags, 0, 0, 0, 8, data1, -1
                    )
                    Quartz.CGEventPost(Quartz.kCGHIDEventTap, ev.CGEvent())
                continue
            except Exception:
                pass

        if key_code in (0, 1):
            sign = "+" if key_code == 0 else "-"
            script = f'set volume output volume ((output volume of (get volume settings)) {sign} 4)'
        else:
            k = 145 if key_code == 2 else 144
            script = f'tell application "System Events" to key code {k}'
        subprocess.run(['osascript', '-e', script], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def change_mac_volume(steps: int):
    key = 0 if steps > 0 else 1
    send_system_media_key(key, repeat=abs(steps))


def change_mac_brightness(steps: int):
    key = 2 if steps > 0 else 3
    send_system_media_key(key, repeat=abs(steps))


def mac_switch_space(direction: str):
    key_codes = {'left': 123, 'right': 124, 'up': 126, 'down': 125}
    code = key_codes.get(direction)
    if not code:
        return

    if USE_QUARTZ:
        try:
            ctrl_down = CG.CGEventCreateKeyboardEvent(None, 59, True)
            CG.CGEventPost(CG.kCGHIDEventTap, ctrl_down)

            k_down = CG.CGEventCreateKeyboardEvent(None, code, True)
            CG.CGEventSetFlags(k_down, CG.kCGEventFlagMaskControl)
            CG.CGEventPost(CG.kCGHIDEventTap, k_down)

            k_up = CG.CGEventCreateKeyboardEvent(None, code, False)
            CG.CGEventSetFlags(k_up, CG.kCGEventFlagMaskControl)
            CG.CGEventPost(CG.kCGHIDEventTap, k_up)

            ctrl_up = CG.CGEventCreateKeyboardEvent(None, 59, False)
            CG.CGEventPost(CG.kCGHIDEventTap, ctrl_up)
        except Exception:
            pass

    def _run_applescript():
        script = f'tell application "System Events" to key code {code} using control down'
        subprocess.run(['osascript', '-e', script], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    threading.Thread(target=_run_applescript, daemon=True).start()


def dist_2d(p1, p2):
    return math.hypot(p1.x - p2.x, p1.y - p2.y)


def is_finger_extended(landmarks, tip_idx, pip_idx, wrist_idx=0):
    return dist_2d(landmarks[tip_idx], landmarks[wrist_idx]) > dist_2d(landmarks[pip_idx], landmarks[wrist_idx]) * 1.05


def check_is_thumbs_up(landmarks):
    wrist = landmarks[0]
    thumb_tip = landmarks[4]
    thumb_mcp = landmarks[2]

    thumb_pointing_up = thumb_tip.y < wrist.y and thumb_tip.y < thumb_mcp.y

    index_curled = not is_finger_extended(landmarks, 8, 6, 0)
    middle_curled = not is_finger_extended(landmarks, 12, 10, 0)
    ring_curled = not is_finger_extended(landmarks, 16, 14, 0)
    pinky_curled = not is_finger_extended(landmarks, 20, 18, 0)

    return thumb_pointing_up and index_curled and middle_curled and ring_curled and pinky_curled


def draw_hand(frame, landmarks, w, h, is_anchored, is_dragging, is_suspended, is_scrolling, is_three_finger, is_volume, is_brightness):
    pts = [(int(lm.x * w), int(lm.y * h)) for lm in landmarks]

    if is_suspended:
        line_color = (100, 100, 100)
    elif is_volume:
        line_color = (255, 120, 0)
    elif is_brightness:
        line_color = (0, 255, 255)
    elif is_three_finger:
        line_color = (255, 0, 255)
    elif is_scrolling:
        line_color = (255, 255, 0)
    elif is_dragging:
        line_color = (0, 0, 255)
    elif is_anchored:
        line_color = (0, 220, 255)
    else:
        line_color = (0, 255, 200)

    for p1_idx, p2_idx in HAND_CONNECTIONS:
        cv2.line(frame, pts[p1_idx], pts[p2_idx], line_color, 2, cv2.LINE_AA)

    for i, pt in enumerate(pts):
        if is_volume and i in (8, 20):
            color = (255, 120, 0)
            radius = 8
        elif is_brightness and i in (8, 12, 16, 20):
            color = (0, 255, 255)
            radius = 8
        elif is_three_finger and i in (8, 12, 16):
            color = (255, 0, 255)
            radius = 8
        elif is_scrolling and i in (8, 12):
            color = (255, 255, 0)
            radius = 7
        elif i in (4, 8):
            color = (0, 0, 255) if is_dragging else ((0, 255, 255) if is_anchored else (0, 140, 255))
            radius = 7 if (is_anchored or is_dragging) else 5
        else:
            color = (180, 180, 180) if is_suspended else (255, 255, 255)
            radius = 3
        cv2.circle(frame, pt, radius, color, -1, cv2.LINE_AA)

    if is_anchored and not is_suspended:
        cv2.circle(frame, pts[8], 16, (0, 255, 255), 2, cv2.LINE_AA)


def main():
    print("=" * 68)
    print("  Mac Hand Gesture Controller (v11 - Robust & Tested)")
    print("=" * 68)
    print("Controls & Gestures:")
    print("  👉 1 Finger (Index)          : Move Cursor, Anchor Lock, Click, Drag")
    print("  ✌️ 2 Fingers (Index+Middle)  : Fluid Smooth Scroll (move up/down)")
    print("  🖐️ 3 Fingers (Index+Mid+Ring): Slide Desktops / Mission Control")
    print("  ☀️ 4 Fingers Up (Hold ~0.45s): Brightness Control (move up/down)")
    print("  🤘 Rock On (Hold ~0.35s)     : Volume Control (move up/down)")
    print("  ✊ Closed Fist               : Quick Pause (stops cursor)")
    print("  👍 Thumbs Up (Hold ~0.55s)   : SUSPEND / RESUME Toggle")
    print("  ⌨️ Press 'q' in camera window: Quit")
    print("  ⌨️ Press 'h' in camera window: Toggle HUD preview")
    print("=" * 68)

    ensure_model_file()

    base_options = python.BaseOptions(model_asset_path=MODEL_FILE)
    options = vision.HandLandmarkerOptions(
        base_options=base_options,
        running_mode=vision.RunningMode.VIDEO,
        num_hands=1,
        min_hand_detection_confidence=0.65,
        min_tracking_confidence=0.65
    )
    detector = vision.HandLandmarker.create_from_options(options)

    cap = cv2.VideoCapture(0, cv2.CAP_AVFOUNDATION)
    if not cap.isOpened():
        cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("\n❌ Error: Unable to access camera. Check macOS permissions.")
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAM_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAM_HEIGHT)

    cursor_x, cursor_y = SCREEN_W // 2, SCREEN_H // 2
    anchor_x, anchor_y = cursor_x, cursor_y
    is_anchored = False
    is_mouse_down = False
    is_dragging = False
    pinch_start_time = None
    last_release_time = 0
    last_right_click_time = 0

    # Motion accumulators & Engagement timers
    prev_scroll_y = None
    scroll_accumulator = 0.0

    prev_volume_y = None
    volume_accumulator = 0.0
    volume_start_time = None

    prev_brightness_y = None
    brightness_accumulator = 0.0
    brightness_start_time = None

    # 3-Finger Swipe State
    swipe_start_x = None
    swipe_start_y = None
    swipe_cooldown_until = 0

    # Suspend / Resume with Thumbs Up (with Latch)
    is_suspended = False
    thumbs_up_start_time = None
    thumbs_up_latched = False

    show_hud = True
    prev_frame_time = time.time()
    start_timestamp_ms = int(time.time() * 1000)

    min_x = int(FRAME_MARGIN_X * CAM_WIDTH)
    max_x = int((1.0 - FRAME_MARGIN_X) * CAM_WIDTH)
    min_y = int(FRAME_MARGIN_Y * CAM_HEIGHT)
    max_y = int((1.0 - FRAME_MARGIN_Y) * CAM_HEIGHT)

    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            time.sleep(0.01)
            continue

        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        current_timestamp_ms = int(time.time() * 1000) - start_timestamp_ms
        if current_timestamp_ms <= 0:
            current_timestamp_ms = 1

        result = detector.detect_for_video(mp_image, current_timestamp_ms)

        now = time.time()
        fps = int(1.0 / (now - prev_frame_time)) if (now - prev_frame_time) > 0 else 0
        prev_frame_time = now

        status_text = "Searching Hand..."
        status_color = (120, 120, 120)
        is_scrolling = False
        is_three_finger = False
        is_volume = False
        is_brightness = False

        if result.hand_landmarks:
            landmarks = result.hand_landmarks[0]

            thumb_tip = landmarks[4]
            index_tip = landmarks[8]
            middle_tip = landmarks[12]
            ring_tip = landmarks[16]
            pinky_tip = landmarks[20]

            index_up = is_finger_extended(landmarks, 8, 6, 0)
            middle_up = is_finger_extended(landmarks, 12, 10, 0)
            ring_up = is_finger_extended(landmarks, 16, 14, 0)
            pinky_up = is_finger_extended(landmarks, 20, 18, 0)

            thumbs_up = check_is_thumbs_up(landmarks)

            # --- 1. THUMBS UP TOGGLE SUSPEND / RESUME (LATCHED) ---
            if thumbs_up:
                if not thumbs_up_latched:
                    if thumbs_up_start_time is None:
                        thumbs_up_start_time = now

                    hold_progress = now - thumbs_up_start_time
                    target_state = "RESUME" if is_suspended else "SUSPEND"
                    progress_pct = min(100, int(hold_progress / THUMBS_UP_HOLD_TIME * 100))
                    status_text = f"👍 HOLDING FOR {target_state} ({progress_pct}%)"
                    status_color = (0, 255, 255)

                    if hold_progress >= THUMBS_UP_HOLD_TIME:
                        is_suspended = not is_suspended
                        thumbs_up_start_time = None
                        thumbs_up_latched = True  # Latch: prevent toggling again until hand is lowered!

                        if is_mouse_down:
                            mac_mouse_up(cursor_x, cursor_y)
                            is_mouse_down = False
                            is_dragging = False

                        if is_suspended:
                            print("\n⏸️ Tracking SUSPENDED (Give 👍 Thumbs Up to Resume)")
                        else:
                            print("\n▶️ Tracking RESUMED (Active)")
                else:
                    status_text = "👍 THUMBS UP (Release to Reset)"
                    status_color = (0, 200, 255)
            else:
                thumbs_up_start_time = None
                thumbs_up_latched = False  # Unlatch as soon as hand changes pose

            # --- 2. PROCESS GESTURES IF ACTIVE ---
            if is_suspended:
                if not thumbs_up:
                    status_text = "⏸️ SUSPENDED (Give 👍 to Resume)"
                    status_color = (130, 130, 130)
            else:
                is_fist = not index_up and not middle_up and not ring_up and not pinky_up and not thumbs_up
                is_horns = index_up and pinky_up and not middle_up and not ring_up
                is_four_fingers = index_up and middle_up and ring_up and pinky_up

                if is_fist:
                    status_text = "⏸️ PAUSED (Fist)"
                    status_color = (0, 165, 255)
                    if is_mouse_down:
                        mac_mouse_up(cursor_x, cursor_y)
                        is_mouse_down = False
                        is_dragging = False
                    is_anchored = False
                    pinch_start_time = None
                    prev_scroll_y = None
                    prev_volume_y = None
                    volume_start_time = None
                    prev_brightness_y = None
                    brightness_start_time = None
                    swipe_start_x = None

                elif is_horns:
                    # ==============================================================
                    # --- 🤘 VOLUME CONTROL (ENGAGEMENT GATE: 0.35s) ---
                    # ==============================================================
                    is_volume = True
                    brightness_start_time = None
                    prev_brightness_y = None
                    prev_scroll_y = None
                    swipe_start_x = None
                    if is_mouse_down:
                        mac_mouse_up(cursor_x, cursor_y)
                        is_mouse_down = False
                        is_dragging = False
                    is_anchored = False

                    curr_y = (index_tip.y + pinky_tip.y) / 2.0

                    if volume_start_time is None:
                        volume_start_time = now
                        prev_volume_y = curr_y

                    hold_time = now - volume_start_time

                    if hold_time < VOLUME_ENGAGE_TIME:
                        progress = int(hold_time / VOLUME_ENGAGE_TIME * 100)
                        status_text = f"🤘 HOLDING FOR VOLUME ({progress}%)"
                        status_color = (255, 120, 0)
                        prev_volume_y = curr_y
                    else:
                        delta_y = curr_y - prev_volume_y
                        volume_accumulator += -delta_y * MEDIA_GESTURE_SENSITIVITY
                        steps = int(volume_accumulator)

                        if steps != 0:
                            change_mac_volume(steps)
                            volume_accumulator -= steps
                            direction_str = "▲ UP" if steps > 0 else "▼ DOWN"
                            status_text = f"🔊 VOLUME {direction_str}"
                            status_color = (255, 120, 0)
                        else:
                            status_text = "🔊 VOLUME ENGAGED (Move Up/Down)"
                            status_color = (255, 120, 0)

                        prev_volume_y = curr_y

                elif is_four_fingers:
                    # ==============================================================
                    # --- ☀️ BRIGHTNESS CONTROL (ENGAGEMENT GATE: 0.45s) ---
                    # ==============================================================
                    is_brightness = True
                    volume_start_time = None
                    prev_volume_y = None
                    prev_scroll_y = None
                    swipe_start_x = None
                    if is_mouse_down:
                        mac_mouse_up(cursor_x, cursor_y)
                        is_mouse_down = False
                        is_dragging = False
                    is_anchored = False

                    curr_y = (index_tip.y + middle_tip.y + ring_tip.y + pinky_tip.y) / 4.0

                    if brightness_start_time is None:
                        brightness_start_time = now
                        prev_brightness_y = curr_y

                    hold_time = now - brightness_start_time

                    if hold_time < BRIGHTNESS_ENGAGE_TIME:
                        progress = int(hold_time / BRIGHTNESS_ENGAGE_TIME * 100)
                        status_text = f"☀️ HOLD 4 FINGERS ({progress}%)"
                        status_color = (0, 255, 255)
                        prev_brightness_y = curr_y
                    else:
                        delta_y = curr_y - prev_brightness_y
                        brightness_accumulator += -delta_y * MEDIA_GESTURE_SENSITIVITY
                        steps = int(brightness_accumulator)

                        if steps != 0:
                            change_mac_brightness(steps)
                            brightness_accumulator -= steps
                            direction_str = "▲ UP" if steps > 0 else "▼ DOWN"
                            status_text = f"☀️ BRIGHTNESS {direction_str}"
                            status_color = (0, 255, 255)
                        else:
                            status_text = "☀️ BRIGHTNESS ENGAGED (Move Up/Down)"
                            status_color = (0, 255, 255)

                        prev_brightness_y = curr_y

                elif index_up and middle_up and ring_up and not pinky_up:
                    # 3-Finger Swipe
                    is_three_finger = True
                    volume_start_time = None
                    brightness_start_time = None
                    prev_volume_y = None
                    prev_brightness_y = None
                    prev_scroll_y = None

                    if is_mouse_down:
                        mac_mouse_up(cursor_x, cursor_y)
                        is_mouse_down = False
                        is_dragging = False
                    is_anchored = False

                    curr_x = (index_tip.x + middle_tip.x + ring_tip.x) / 3.0
                    curr_y = (index_tip.y + middle_tip.y + ring_tip.y) / 3.0

                    if now > swipe_cooldown_until:
                        if swipe_start_x is None:
                            swipe_start_x = curr_x
                            swipe_start_y = curr_y
                            status_text = "🖐️ 3-FINGER SWIPE READY"
                            status_color = (255, 0, 255)
                        else:
                            dx = curr_x - swipe_start_x
                            dy = curr_y - swipe_start_y

                            if abs(dx) > SWIPE_DIST_THRESHOLD and abs(dx) > abs(dy) * 1.1:
                                if dx > 0:
                                    mac_switch_space('left')
                                    status_text = "◀️ SLIDE DESKTOP (LEFT)"
                                else:
                                    mac_switch_space('right')
                                    status_text = "▶️ SLIDE DESKTOP (RIGHT)"

                                status_color = (255, 0, 255)
                                swipe_cooldown_until = now + SWIPE_COOLDOWN
                                swipe_start_x = None
                                swipe_start_y = None

                            elif abs(dy) > SWIPE_DIST_THRESHOLD and abs(dy) > abs(dx) * 1.1:
                                if dy < 0:
                                    mac_switch_space('up')
                                    status_text = "🔼 MISSION CONTROL"
                                else:
                                    mac_switch_space('down')
                                    status_text = "🔽 APP WINDOWS"

                                status_color = (255, 0, 255)
                                swipe_cooldown_until = now + SWIPE_COOLDOWN
                                swipe_start_x = None
                                swipe_start_y = None
                            else:
                                status_text = "🖐️ 3-FINGER SWIPE..."
                                status_color = (255, 0, 255)
                    else:
                        status_text = "🖐️ SWIPED!"
                        status_color = (255, 0, 255)

                elif index_up and middle_up and not ring_up and not pinky_up:
                    # 2-Finger Fluid Scroll
                    is_scrolling = True
                    swipe_start_x = None
                    volume_start_time = None
                    brightness_start_time = None
                    prev_volume_y = None
                    prev_brightness_y = None

                    if is_mouse_down:
                        mac_mouse_up(cursor_x, cursor_y)
                        is_mouse_down = False
                        is_dragging = False
                    is_anchored = False
                    pinch_start_time = None

                    curr_y = (index_tip.y + middle_tip.y) / 2.0

                    if prev_scroll_y is not None:
                        delta_y = curr_y - prev_scroll_y

                        direction = 1 if not SCROLL_INVERT else -1
                        scroll_delta = -delta_y * SCROLL_SENSITIVITY * direction

                        speed = abs(delta_y)
                        if speed > 0.02:
                            scroll_delta *= 1.5

                        scroll_accumulator += scroll_delta
                        lines_to_scroll = int(scroll_accumulator)

                        if lines_to_scroll != 0:
                            mac_scroll_lines(lines_to_scroll)
                            scroll_accumulator -= lines_to_scroll

                            dir_symbol = "▲ UP" if lines_to_scroll > 0 else "▼ DOWN"
                            status_text = f"📜 SCROLLING {dir_symbol}"
                            status_color = (255, 255, 0)
                        else:
                            status_text = "📜 SCROLL READY"
                            status_color = (200, 200, 0)
                    else:
                        status_text = "📜 SCROLL READY"
                        status_color = (200, 200, 0)

                    prev_scroll_y = curr_y

                elif not thumbs_up:
                    # 1-Finger Pointer, Click, Drag
                    prev_scroll_y = None
                    prev_volume_y = None
                    prev_brightness_y = None
                    volume_start_time = None
                    brightness_start_time = None
                    scroll_accumulator = 0.0
                    volume_accumulator = 0.0
                    brightness_accumulator = 0.0
                    swipe_start_x = None

                    raw_cam_x = index_tip.x * w
                    raw_cam_y = index_tip.y * h

                    clamped_x = max(min_x, min(max_x, raw_cam_x))
                    clamped_y = max(min_y, min(max_y, raw_cam_y))

                    norm_x = (clamped_x - min_x) / (max_x - min_x)
                    norm_y = (clamped_y - min_y) / (max_y - min_y)

                    target_screen_x = norm_x * SCREEN_W
                    target_screen_y = norm_y * SCREEN_H

                    d_index_thumb = dist_2d(index_tip, thumb_tip)
                    d_middle_thumb = dist_2d(middle_tip, thumb_tip)

                    # Anchor Lock
                    if d_index_thumb < PINCH_PREPARE_DIST and not is_dragging:
                        if not is_anchored:
                            is_anchored = True
                            anchor_x, anchor_y = cursor_x, cursor_y
                    elif d_index_thumb > PINCH_RELEASE_DIST and not is_dragging:
                        if is_anchored:
                            is_anchored = False
                            last_release_time = now

                    in_release_cooldown = (now - last_release_time) < RELEASE_COOLDOWN

                    if is_dragging:
                        new_cursor_x = (1 - SMOOTHING_ALPHA) * cursor_x + SMOOTHING_ALPHA * target_screen_x
                        new_cursor_y = (1 - SMOOTHING_ALPHA) * cursor_y + SMOOTHING_ALPHA * target_screen_y
                        cursor_x, cursor_y = new_cursor_x, new_cursor_y
                        mac_mouse_drag(cursor_x, cursor_y)
                        status_text = "✊ DRAGGING"
                        status_color = (0, 0, 255)

                    elif not is_anchored and not in_release_cooldown:
                        new_cursor_x = (1 - SMOOTHING_ALPHA) * cursor_x + SMOOTHING_ALPHA * target_screen_x
                        new_cursor_y = (1 - SMOOTHING_ALPHA) * cursor_y + SMOOTHING_ALPHA * target_screen_y

                        if math.hypot(new_cursor_x - cursor_x, new_cursor_y - cursor_y) > JITTER_THRESHOLD:
                            cursor_x, cursor_y = new_cursor_x, new_cursor_y
                            mac_move_mouse(cursor_x, cursor_y)

                    # Pinch Click / Drag
                    if d_index_thumb < PINCH_CLICK_DIST:
                        if pinch_start_time is None:
                            pinch_start_time = now

                        pinch_duration = now - pinch_start_time

                        if not is_mouse_down:
                            click_pos_x = anchor_x if is_anchored else cursor_x
                            click_pos_y = anchor_y if is_anchored else cursor_y
                            mac_mouse_down(click_pos_x, click_pos_y)
                            is_mouse_down = True

                        if pinch_duration >= DRAG_THRESHOLD_TIME:
                            is_dragging = True
                            status_text = "✊ DRAGGING"
                            status_color = (0, 0, 255)
                        else:
                            status_text = "🎯 CLICK DOWN"
                            status_color = (0, 255, 0)
                    else:
                        if is_mouse_down:
                            mac_mouse_up(cursor_x, cursor_y)
                            is_mouse_down = False
                            is_dragging = False
                            last_release_time = now
                            status_text = "✅ CLICK COMPLETED"
                            status_color = (0, 255, 0)
                        pinch_start_time = None

                    # Right Click
                    if d_middle_thumb < PINCH_RIGHT_DIST and not is_dragging and not is_mouse_down:
                        if (now - last_right_click_time) > 0.6:
                            target_click_x = anchor_x if is_anchored else cursor_x
                            target_click_y = anchor_y if is_anchored else cursor_y
                            mac_right_click(target_click_x, target_click_y)
                            last_right_click_time = now
                            status_text = "👉 RIGHT CLICK"
                            status_color = (255, 0, 255)

                    if status_text.startswith("Searching") and index_up:
                        if is_anchored:
                            status_text = "🔒 ANCHOR LOCKED"
                            status_color = (0, 255, 255)
                        else:
                            status_text = "TRACKING (Moving)"
                            status_color = (0, 255, 0)

            if show_hud:
                draw_hand(frame, landmarks, w, h, is_anchored, is_dragging, is_suspended, is_scrolling, is_three_finger, is_volume, is_brightness)

        if show_hud:
            cv2.rectangle(frame, (min_x, min_y), (max_x, max_y), (70, 70, 70), 1)
            cv2.putText(frame, "Screen Boundary", (min_x + 5, min_y - 8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (160, 160, 160), 1)

            cv2.rectangle(frame, (10, 10), (430, 50), (25, 25, 25), -1)
            cv2.circle(frame, (28, 30), 8, status_color, -1)
            cv2.putText(frame, status_text, (45, 36),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.53, (255, 255, 255), 2)

            cv2.putText(frame, f"FPS: {fps}", (w - 90, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 0), 1)
            cv2.putText(frame, "[h] Toggle HUD | [q] Quit", (12, h - 15),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1)

            cv2.imshow("Mac Hand Gesture Mouse", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            print("\nExiting gesture controller...")
            break
        elif key == ord('h'):
            show_hud = not show_hud
            if not show_hud:
                cv2.destroyAllWindows()

    if is_mouse_down:
        mac_mouse_up(cursor_x, cursor_y)
    cap.release()
    cv2.destroyAllWindows()
    print("Gesture controller closed.")


if __name__ == "__main__":
    main()
