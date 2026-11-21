"""Small helpers shared by the demos: file paths, loading images and drawing results."""

import sys
from pathlib import Path

import cv2
import mediapipe as mp
import numpy as np

HERE = Path(__file__).resolve().parent
MODELS = HERE / "models"
SAMPLES = HERE / "samples"
OUTPUTS = HERE / "outputs"

# Colors are in OpenCV's blue-green-red order.
GREEN, RED, BLUE, YELLOW, WHITE, BLACK = (60, 200, 60), (60, 60, 230), (230, 120, 0), (0, 220, 255), (255, 255, 255), (20, 20, 20)


def model(name):
    """Path of a downloaded model; run download_models.py first."""
    path = MODELS / name
    if not path.exists():
        sys.exit(f"{path} not found. Run: python download_models.py")
    return str(path)


def input_path(default):
    """The file given on the command line, or the default sample."""
    return Path(sys.argv[1]) if len(sys.argv) > 1 else SAMPLES / default


# Small images are enlarged to at least this height before drawing, so labels stay readable.
MIN_DRAWING_HEIGHT = 720


def load_image(path):
    """Read an image both as a MediaPipe Image (for the model) and as an OpenCV array (for drawing).

    The model always gets the original image; only the copy used for drawing is enlarged.
    """
    image = mp.Image.create_from_file(str(path))
    drawing = cv2.cvtColor(image.numpy_view(), cv2.COLOR_RGB2BGR)
    if drawing.shape[0] < MIN_DRAWING_HEIGHT:
        scale = MIN_DRAWING_HEIGHT / drawing.shape[0]
        drawing = cv2.resize(drawing, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    return image, drawing


def box_corners(box, image, drawing):
    """Corners of a detection box, scaled from the original image to the (maybe enlarged) drawing."""
    scale = drawing.shape[1] / image.width
    top_left = (int(box.origin_x * scale), int(box.origin_y * scale))
    bottom_right = (int((box.origin_x + box.width) * scale), int((box.origin_y + box.height) * scale))
    return top_left, bottom_right


def add_panel(drawing, lines, color=BLACK):
    """Add a white strip under the picture with one line of text per item."""
    line_height = 30
    panel = np.full((line_height * len(lines) + 16, drawing.shape[1], 3), 255, np.uint8)
    for i, line in enumerate(lines):
        cv2.putText(panel, line, (12, 28 + line_height * i), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2, cv2.LINE_AA)
    return np.vstack([drawing, panel])


def pixel(point, drawing):
    """Turn a landmark's 0-1 coordinates into pixel coordinates."""
    height, width = drawing.shape[:2]
    return int(point.x * width), int(point.y * height)


def draw_text(drawing, text, origin, color=WHITE, scale=0.6):
    """Text with a dark outline, readable on any background."""
    cv2.putText(drawing, text, origin, cv2.FONT_HERSHEY_SIMPLEX, scale, BLACK, 4, cv2.LINE_AA)
    cv2.putText(drawing, text, origin, cv2.FONT_HERSHEY_SIMPLEX, scale, color, 2, cv2.LINE_AA)


def draw_landmarks(drawing, points, connections=(), color=GREEN, radius=3):
    """Draw landmarks as dots, joined by lines where the model defines connections."""
    for connection in connections:
        cv2.line(drawing, pixel(points[connection.start], drawing), pixel(points[connection.end], drawing),
                 WHITE, 2, cv2.LINE_AA)
    for point in points:
        cv2.circle(drawing, pixel(point, drawing), radius, color, -1, cv2.LINE_AA)


def save(drawing, name):
    """Save the annotated image to outputs/ and print where it went."""
    OUTPUTS.mkdir(exist_ok=True)
    path = OUTPUTS / name
    cv2.imwrite(str(path), drawing)
    print(f"Saved {path.relative_to(HERE)}")
    return path


def cosine_similarity(a, b):
    """How alike two embedding vectors are: 1 = same direction, 0 = unrelated."""
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    return float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b)))
