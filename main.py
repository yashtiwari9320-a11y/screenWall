"""screenWall: draw glowing strokes in the air with your index finger."""

from __future__ import annotations

import time
from datetime import datetime
from pathlib import Path

import cv2
import mediapipe as mp
import numpy as np


WINDOW = "screenWall | Air canvas"
COLORS = [
    (255, 112, 66),   # coral
    (71, 230, 255),   # cyan
    (255, 113, 224),  # pink
    (105, 255, 116),  # lime
    (255, 255, 255),  # white
    (60, 145, 255),   # orange
]
COLOR_NAMES = ["Coral", "Cyan", "Pink", "Lime", "White", "Orange"]
BG = (19, 17, 30)


def finger_is_up(hand, tip: int, pip: int) -> bool:
    """Return whether a non-thumb finger is extended in the image."""
    return hand.landmark[tip].y < hand.landmark[pip].y


def draw_text(image, text, pos, scale=0.55, color=(238, 240, 248), thickness=1):
    cv2.putText(image, text, pos, cv2.FONT_HERSHEY_SIMPLEX, scale, color,
                thickness, cv2.LINE_AA)


def main() -> None:
    camera = cv2.VideoCapture(0)
    if not camera.isOpened():
        raise SystemExit("Could not open your camera. Check camera access and try again.")

    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    ok, first = camera.read()
    if not ok:
        camera.release()
        raise SystemExit("Your camera opened but did not return a frame.")

    height, width = first.shape[:2]
    canvas = np.zeros((height, width, 3), dtype=np.uint8)
    glow = np.zeros_like(canvas)
    selected = 1
    brush = max(4, int(height * 0.012))
    previous_point = None
    hover_since = None
    clear_flash_until = 0.0
    saved_flash_until = 0.0
    output_dir = Path("drawings")

    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=1,
        model_complexity=1,
        min_detection_confidence=0.65,
        min_tracking_confidence=0.6,
    )

    cv2.namedWindow(WINDOW, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(WINDOW, width, height)
    try:
        while True:
            ok, frame = camera.read()
            if not ok:
                break
            frame = cv2.flip(frame, 1)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            result = hands.process(rgb)
            point = None
            mode = "Show your hand"
            erasing = False

            if result.multi_hand_landmarks:
                hand = result.multi_hand_landmarks[0]
                tip = hand.landmark[8]
                point = (int(tip.x * width), int(tip.y * height))
                index_up = finger_is_up(hand, 8, 6)
                middle_up = finger_is_up(hand, 12, 10)
                ring_up = finger_is_up(hand, 16, 14)
                pinky_up = finger_is_up(hand, 20, 18)
                erasing = index_up and middle_up
                drawing = index_up and not middle_up and not ring_up and not pinky_up

                # UI geometry is sized from the camera frame.
                panel_x, panel_y = 22, 22
                palette_y = panel_y + 75
                swatch = max(24, int(height * 0.038))
                gap = max(10, int(height * 0.014))
                clear_rect = (width - 154, 24, width - 24, 78)
                on_palette = point[1] in range(palette_y - swatch // 2 - 10,
                                                palette_y + swatch // 2 + 10)
                hovered_color = None
                if on_palette:
                    for i in range(len(COLORS)):
                        cx = panel_x + 23 + i * (swatch + gap)
                        if abs(point[0] - cx) <= swatch // 2 + 8:
                            hovered_color = i
                            break

                in_clear = (clear_rect[0] <= point[0] <= clear_rect[2]
                            and clear_rect[1] <= point[1] <= clear_rect[3])
                if hovered_color is not None:
                    selected = hovered_color
                    mode = "Color selected"
                    previous_point = None
                    hover_since = None
                elif in_clear:
                    mode = "Hold to clear"
                    previous_point = None
                    if hover_since is None:
                        hover_since = time.monotonic()
                    elif time.monotonic() - hover_since >= 1.0:
                        canvas[:] = 0
                        glow[:] = 0
                        clear_flash_until = time.monotonic() + 0.8
                        hover_since = None
                else:
                    hover_since = None
                    if erasing:
                        mode = "Eraser"
                        if previous_point is not None:
                            cv2.line(canvas, previous_point, point, (0, 0, 0),
                                     brush * 4, cv2.LINE_AA)
                            cv2.line(glow, previous_point, point, (0, 0, 0),
                                     brush * 4, cv2.LINE_AA)
                        previous_point = point
                    elif drawing:
                        mode = "Drawing"
                        if previous_point is not None:
                            cv2.line(canvas, previous_point, point, COLORS[selected],
                                     brush, cv2.LINE_AA)
                            cv2.line(glow, previous_point, point, COLORS[selected],
                                     brush * 2, cv2.LINE_AA)
                        previous_point = point
                    else:
                        mode = "Raise index finger to draw"
                        previous_point = None

                # Draw a small tracking skeleton over the live camera.
                mp.solutions.drawing_utils.draw_landmarks(
                    frame, hand, mp_hands.HAND_CONNECTIONS,
                    mp.solutions.drawing_utils.DrawingSpec(color=(105, 90, 85), thickness=1, circle_radius=2),
                    mp.solutions.drawing_utils.DrawingSpec(color=COLORS[selected], thickness=2, circle_radius=2),
                )
                cursor_color = (235, 245, 255) if erasing else COLORS[selected]
                cv2.circle(frame, point, brush, cursor_color, 2, cv2.LINE_AA)
                if in_clear and hover_since is not None:
                    progress = min(1.0, (time.monotonic() - hover_since) / 1.0)
                    cv2.ellipse(frame, (point[0], point[1]), (25, 25), -90, 0,
                                int(360 * progress), (110, 235, 255), 3, cv2.LINE_AA)
            else:
                previous_point = None
                hover_since = None

            # A soft blur makes the saved strokes and live strokes glow.
            blurred = cv2.GaussianBlur(glow, (0, 0), sigmaX=max(3, brush * 1.5))
            view = cv2.addWeighted(frame, 1.0, blurred, 0.75, 0)
            view = cv2.addWeighted(view, 1.0, canvas, 1.0, 0)

            # HUD panel and color palette.
            cv2.rectangle(view, (14, 14), (390, 136), (22, 21, 36), -1)
            cv2.rectangle(view, (14, 14), (390, 136), (76, 73, 103), 1)
            draw_text(view, "screenWall", (28, 45), 0.72, (245, 244, 255), 2)
            draw_text(view, "AIR CANVAS  /  HOVER TO PICK A COLOR", (29, 65), 0.38, (155, 156, 184))
            palette_y = 98
            swatch = max(24, int(height * 0.038))
            gap = max(10, int(height * 0.014))
            for i, color in enumerate(COLORS):
                cx = 43 + i * (swatch + gap)
                cv2.circle(view, (cx, palette_y), swatch // 2, color, -1, cv2.LINE_AA)
                if i == selected:
                    cv2.circle(view, (cx, palette_y), swatch // 2 + 4, (245, 245, 255), 2, cv2.LINE_AA)
            draw_text(view, COLOR_NAMES[selected], (300, 104), 0.43, COLORS[selected], 1)

            clear_rect = (width - 154, 24, width - 24, 78)
            cv2.rectangle(view, clear_rect[:2], clear_rect[2:], (35, 29, 48), -1, cv2.LINE_AA)
            cv2.rectangle(view, clear_rect[:2], clear_rect[2:], (105, 92, 123), 1, cv2.LINE_AA)
            draw_text(view, "CLEAR CANVAS", (width - 139, 57), 0.48, (243, 223, 239), 1)
            if hover_since is not None and point is not None and clear_rect[0] <= point[0] <= clear_rect[2] and clear_rect[1] <= point[1] <= clear_rect[3]:
                progress = min(1.0, (time.monotonic() - hover_since) / 1.0)
                cv2.rectangle(view, (clear_rect[0], clear_rect[3] - 4),
                              (clear_rect[0] + int((clear_rect[2] - clear_rect[0]) * progress), clear_rect[3] - 1),
                              (105, 230, 255), -1)

            cv2.rectangle(view, (14, height - 54), (width - 14, height - 14), (22, 21, 36), -1)
            draw_text(view, f"{mode.upper()}  |  {brush}px", (28, height - 29), 0.46, (225, 222, 240), 1)
            draw_text(view, "INDEX: DRAW   TWO FINGERS: ERASE   [ / ]: SIZE   S: SAVE   C: CLEAR   Q: QUIT",
                      (max(300, int(width * 0.35)), height - 29), 0.40, (170, 167, 190), 1)

            now = time.monotonic()
            if now < clear_flash_until:
                draw_text(view, "Canvas cleared", (width // 2 - 85, height // 2), 0.8, (130, 242, 255), 2)
            if now < saved_flash_until:
                draw_text(view, "Drawing saved", (width // 2 - 82, height // 2), 0.8, (130, 242, 255), 2)

            cv2.imshow(WINDOW, view)
            key = cv2.waitKey(1) & 0xFF
            if key in (ord("q"), 27):
                break
            if key in (ord("c"), ord("C")):
                canvas[:] = 0
                glow[:] = 0
                clear_flash_until = time.monotonic() + 0.8
            if key in (ord("["), ord("-")):
                brush = max(2, brush - 2)
            if key in (ord("]"), ord("+"), ord("=")):
                brush = min(max(24, height // 18), brush + 2)
            if key in (ord("s"), ord("S")):
                output_dir.mkdir(parents=True, exist_ok=True)
                blurred_art = cv2.GaussianBlur(glow, (0, 0), sigmaX=max(3, brush * 1.5))
                artwork = np.full_like(canvas, BG)
                artwork = cv2.addWeighted(artwork, 1.0, blurred_art, 0.8, 0)
                artwork = cv2.addWeighted(artwork, 1.0, canvas, 1.0, 0)
                filename = output_dir / f"screenwall-{datetime.now():%Y%m%d-%H%M%S}.png"
                if cv2.imwrite(str(filename), artwork):
                    saved_flash_until = time.monotonic() + 0.9
                    print(f"Saved {filename}")
    finally:
        hands.close()
        camera.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
