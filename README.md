# screenWall

Draw glowing strokes in the air with your webcam. screenWall mirrors the camera, tracks one hand, and lays neon strokes over the live view.

## Setup

Python 3.10-3.12 is recommended. From this folder:

```bash
python -m venv .venv
```

Activate the environment, then install and launch:

```bash
python -m pip install -r requirements.txt
python main.py
```

On Windows PowerShell, activate with `.venv\Scripts\Activate.ps1`. On macOS/Linux, use `source .venv/bin/activate`.

## Skills demonstrated

- **Python application development** — organizing and running a small, interactive desktop app.
- **Computer vision** — capturing and processing live webcam frames with OpenCV.
- **Hand tracking** — detecting fingertip and finger landmarks with MediaPipe.
- **Gesture recognition** — mapping hand poses and hover gestures to drawing, erasing, color selection, and clearing.
- **Real-time image processing** — rendering smooth strokes, compositing layers, and creating a neon glow with NumPy and OpenCV.
- **Interactive UI design** — drawing a live palette, status display, and controls over the camera view.
- **Image export** — saving the finished canvas as a PNG.
- **Python environment management** — declaring dependencies and using a virtual environment.

## Controls

- Point with only your index finger extended to draw.
- Extend your index and middle fingers together to erase.
- Hover over a palette dot to select its color.
- Hold over **CLEAR CANVAS** for one second, or press `C`, to clear.
- Press `[` / `]` to change brush size.
- Press `S` to save a PNG into `drawings/`.
- Press `Q` or `Esc` to quit.

The first camera device is used. If no camera opens, check your operating system's camera permissions and close other apps that may be using it.
