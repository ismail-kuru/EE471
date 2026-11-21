"""Draw what each face model finds and how each script decides the direction, side by side.

Usage: python visualize.py images/face-1.png images/face-2.png images/face-3.png
Saves one PNG per image and comparison.png with all of them, in the visualizations/ folder.

Left half, Face Landmarker (face_direction.py, used by Cog):
  green dots and white lines: the 478 face points and the face outline
  orange arrow: where the head is turned, longer for a larger yaw angle
Right half, Face Detector / BlazeFace (face_direction_blazeface.py, comparison only):
  green box and 6 labeled points
  cyan line: the middle of the eyes; orange arrow: how far the nose tip moved from it
"""

import sys
from pathlib import Path

import cv2
import mediapipe as mp
import numpy as np
from mediapipe.tasks.python import vision

import face_direction as landmarker_method
import face_direction_blazeface as blazeface_method

OUTPUT_DIR = Path(__file__).resolve().parent / "visualizations"
HEIGHT = 600          # Each half is scaled to this height so the drawings are readable.
PANEL = 120           # White text strip under each half.

# Colors are in OpenCV's blue-green-red order.
GREEN, WHITE, BLACK = (60, 190, 60), (255, 255, 255), (30, 30, 30)
ORANGE, CYAN, YELLOW = (0, 140, 255), (200, 170, 0), (0, 210, 255)
FONT = cv2.FONT_HERSHEY_SIMPLEX
NOSE_TIP = 1  # Face Landmarker's point on the tip of the nose.
BLAZE_NAMES = ["R eye", "L eye", "nose", "mouth", "R ear", "L ear"]


def to_pixel(point, size):
    return int(point.x * size[0]), int(point.y * size[1])


def label(img, text, origin, color, scale=0.55):
    cv2.putText(img, text, origin, FONT, scale, WHITE, 4, cv2.LINE_AA)
    cv2.putText(img, text, origin, FONT, scale, color, 2, cv2.LINE_AA)


def with_panel(img, lines):
    panel = np.full((PANEL, img.shape[1], 3), 255, np.uint8)
    for i, (text, color) in enumerate(lines):
        cv2.putText(panel, text, (10, 28 + 30 * i), FONT, 0.6, color, 2, cv2.LINE_AA)
    return np.vstack([img, panel])


def draw_landmarker(base, size, result):
    img = base.copy()
    points = result.face_landmarks[0]
    for c in vision.FaceLandmarksConnections.FACE_LANDMARKS_CONTOURS:
        cv2.line(img, to_pixel(points[c.start], size), to_pixel(points[c.end], size), WHITE, 2, cv2.LINE_AA)
    for p in points:
        cv2.circle(img, to_pixel(p, size), 1, GREEN, -1, cv2.LINE_AA)

    yaw = landmarker_method.head_yaw(result.facial_transformation_matrixes[0])
    direction = landmarker_method.direction_from_yaw(yaw)
    # A head turned to the person's right (negative yaw) faces the photo's left.
    nose = to_pixel(points[NOSE_TIP], size)
    tip_x = min(max(int(nose[0] + yaw * 4), 12), size[0] - 12)  # Keep the arrow inside the picture.
    tip = (tip_x, nose[1])
    cv2.arrowedLine(img, nose, tip, ORANGE, 4, cv2.LINE_AA, tipLength=0.25)
    cv2.circle(img, nose, 6, ORANGE, -1, cv2.LINE_AA)
    label(img, "Face Landmarker", (10, 26), BLACK, 0.7)
    return with_panel(img, [
        (f"{len(points)} points + head rotation", BLACK),
        (f"yaw {yaw:+.0f} deg (straight within +-{landmarker_method.YAW_THRESHOLD})", BLACK),
        (f"result: {direction}", ORANGE),
    ]), direction


def draw_blazeface(base, size, scale, result):
    img = base.copy()
    detection = result.detections[0]
    box = detection.bounding_box
    cv2.rectangle(img, (int(box.origin_x * scale), int(box.origin_y * scale)),
                  (int((box.origin_x + box.width) * scale), int((box.origin_y + box.height) * scale)), GREEN, 3)
    keypoints = detection.keypoints
    for name, p in zip(BLAZE_NAMES, keypoints):
        x, y = to_pixel(p, size)
        cv2.circle(img, (x, y), 7, YELLOW, -1, cv2.LINE_AA)
        cv2.circle(img, (x, y), 7, BLACK, 1, cv2.LINE_AA)
        label(img, name, (x + 9, y - 6), BLACK, 0.45)

    right_eye, left_eye, nose = (to_pixel(keypoints[i], size) for i in (0, 1, 2))
    middle_x = (right_eye[0] + left_eye[0]) // 2
    cv2.line(img, (middle_x, min(right_eye[1], left_eye[1]) - 30), (middle_x, nose[1] + 30), CYAN, 2, cv2.LINE_AA)
    if abs(nose[0] - middle_x) > 3:
        cv2.arrowedLine(img, (middle_x, nose[1]), nose, ORANGE, 4, cv2.LINE_AA, tipLength=0.3)

    offset = blazeface_method.nose_offset(keypoints)
    direction = blazeface_method.direction_from_offset(offset)
    label(img, "Face Detector (BlazeFace)", (10, 26), BLACK, 0.7)
    return with_panel(img, [
        ("box + 6 points, no rotation", BLACK),
        (f"nose shift {offset:+.2f} (straight within +-{blazeface_method.OFFSET_THRESHOLD})", BLACK),
        (f"result: {direction}", ORANGE),
    ]), direction


def annotate(image_path, landmarker, detector):
    image = mp.Image.create_from_file(str(image_path))
    scale = HEIGHT / image.height
    size = (int(image.width * scale), HEIGHT)
    base = cv2.resize(cv2.cvtColor(image.numpy_view(), cv2.COLOR_RGB2BGR), size, interpolation=cv2.INTER_CUBIC)

    left, a = draw_landmarker(base, size, landmarker.detect(image))
    right, b = draw_blazeface(base, size, scale, detector.detect(image))
    gap = np.full((left.shape[0], 10, 3), 255, np.uint8)
    title = np.full((40, left.shape[1] * 2 + 10, 3), 255, np.uint8)
    cv2.putText(title, Path(image_path).name, (10, 28), FONT, 0.8, BLACK, 2, cv2.LINE_AA)
    return np.vstack([title, np.hstack([left, gap, right])]), a, b


def main():
    if len(sys.argv) < 2:
        sys.exit("Usage: python visualize.py <image> [more images...]")
    OUTPUT_DIR.mkdir(exist_ok=True)
    landmarker = landmarker_method.create_landmarker()
    detector = blazeface_method.create_detector()
    pictures = []
    for image_path in sys.argv[1:]:
        picture, a, b = annotate(image_path, landmarker, detector)
        out = OUTPUT_DIR / f"{Path(image_path).stem}.png"
        cv2.imwrite(str(out), picture)
        pictures.append(picture)
        print(f"{image_path}: Face Landmarker={a}, BlazeFace={b} -> {out.name}")

    width = max(p.shape[1] for p in pictures)
    padded = [np.pad(p, ((0, 0), (0, width - p.shape[1]), (0, 0)), constant_values=255) for p in pictures]
    gap = np.full((14, width, 3), 255, np.uint8)
    stacked = [padded[0]]
    for p in padded[1:]:
        stacked += [gap, p]
    cv2.imwrite(str(OUTPUT_DIR / "comparison.png"), np.vstack(stacked))
    print("comparison.png saved")


if __name__ == "__main__":
    main()
