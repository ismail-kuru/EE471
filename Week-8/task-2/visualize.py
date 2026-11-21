"""Draw the detected pose and compare the two raised-arm rules on each image.

Usage: python visualize.py images/pose-1.jpg images/pose-2.jpg images/pose-3.jpg
Saves one annotated PNG per image, comparison.png with all of them side by side, and
rules.png showing at which arm angles the two rules disagree, in the visualizations/ folder.

In each picture:
  - gray lines and white dots: the body points MediaPipe found
  - orange: the person's left arm, blue: the right arm, with its angle above horizontal
  - dashed magenta line (A): how high the wrist must be under the "margin" rule
  - cyan line (B): the MIN_ANGLE degree line the arm must reach under the "angle" rule
"""

import math
import sys
from pathlib import Path

import cv2
import mediapipe as mp
import numpy as np
from mediapipe.tasks.python import vision

from arm_up import (LEFT_SHOULDER, LEFT_WRIST, MARGIN, MIN_ANGLE, RIGHT_SHOULDER, RIGHT_WRIST,
                    arm_angle, create_landmarker, torso_length, which_arm_is_up)

OUTPUT_DIR = Path(__file__).resolve().parent / "visualizations"
HEIGHT = 800          # Every picture is scaled to this height so the drawings are readable.
PANEL = 165           # Height of the white text panel under each picture.

# Colors are in OpenCV's blue-green-red order.
GRAY, WHITE, BLACK = (160, 160, 160), (255, 255, 255), (30, 30, 30)
ORANGE, BLUE = (0, 140, 255), (220, 110, 0)
MAGENTA, CYAN = (200, 0, 200), (200, 170, 0)
GREEN, RED = (40, 150, 40), (40, 40, 200)
FONT = cv2.FONT_HERSHEY_SIMPLEX


def pixel(point, size):
    return int(point.x * size[0]), int(point.y * size[1])


def dashed_line(img, start, end, color, thickness=2, dash=10):
    """OpenCV has no dashed line, so draw short pieces."""
    length = math.dist(start, end)
    for i in range(0, int(length), dash * 2):
        a = i / length
        b = min(i + dash, length) / length
        p = (int(start[0] + (end[0] - start[0]) * a), int(start[1] + (end[1] - start[1]) * a))
        q = (int(start[0] + (end[0] - start[0]) * b), int(start[1] + (end[1] - start[1]) * b))
        cv2.line(img, p, q, color, thickness, cv2.LINE_AA)


def label(img, text, origin, color, scale=0.6, thickness=2):
    """Text with a white outline so it stays readable on any background, kept inside the picture."""
    (text_width, text_height), _ = cv2.getTextSize(text, FONT, scale, thickness)
    x = min(max(origin[0], 4), img.shape[1] - text_width - 4)
    y = min(max(origin[1], text_height + 4), img.shape[0] - 4)
    origin = (x, y)
    cv2.putText(img, text, origin, FONT, scale, WHITE, thickness + 3, cv2.LINE_AA)
    cv2.putText(img, text, origin, FONT, scale, color, thickness, cv2.LINE_AA)


def draw_arm(img, points, size, shoulder_id, wrist_id, color, name):
    shoulder, wrist = points[shoulder_id], points[wrist_id]
    s, w = pixel(shoulder, size), pixel(wrist, size)
    arm_length = math.dist(s, w)
    outward = 1 if w[0] >= s[0] else -1  # Draw the guide lines on the side the arm points to.

    # Rule A: the wrist must be above this height.
    a_y = int((shoulder.y - MARGIN * torso_length(points)) * size[1])
    dashed_line(img, (s[0] - 70, a_y), (s[0] + 70, a_y), MAGENTA)
    label(img, "A", (s[0] + outward * 78 - (12 if outward < 0 else 0), a_y + 6), MAGENTA, 0.6)

    # Rule B: the arm must point at least MIN_ANGLE degrees above horizontal.
    rad = math.radians(MIN_ANGLE)
    b_end = (int(s[0] + outward * arm_length * math.cos(rad)), int(s[1] - arm_length * math.sin(rad)))
    cv2.line(img, s, b_end, CYAN, 2, cv2.LINE_AA)
    label(img, "B", (b_end[0] + outward * 6 - (14 if outward < 0 else 0), b_end[1]), CYAN, 0.6)

    # The arm itself, from shoulder to wrist, with its angle.
    cv2.line(img, s, w, color, 4, cv2.LINE_AA)
    for p in (s, w):
        cv2.circle(img, p, 8, color, -1, cv2.LINE_AA)
        cv2.circle(img, p, 8, WHITE, 2, cv2.LINE_AA)
    angle = arm_angle(wrist, shoulder, size)
    label(img, f"{name} {angle:+.0f} deg", (w[0] - 60, w[1] - 16), color, 0.6)
    return angle


def annotate(image_path, landmarker):
    image = mp.Image.create_from_file(str(image_path))
    points = landmarker.detect(image).pose_landmarks[0]
    original_size = (image.width, image.height)

    scale = HEIGHT / image.height
    size = (int(image.width * scale), HEIGHT)
    img = cv2.cvtColor(image.numpy_view(), cv2.COLOR_RGB2BGR)
    img = cv2.resize(img, size, interpolation=cv2.INTER_CUBIC)

    # The whole skeleton, so the detection itself can be checked.
    for connection in vision.PoseLandmarksConnections.POSE_LANDMARKS:
        cv2.line(img, pixel(points[connection.start], size), pixel(points[connection.end], size),
                 GRAY, 2, cv2.LINE_AA)
    for point in points:
        cv2.circle(img, pixel(point, size), 4, WHITE, -1, cv2.LINE_AA)
        cv2.circle(img, pixel(point, size), 4, BLACK, 1, cv2.LINE_AA)

    left_angle = draw_arm(img, points, size, LEFT_SHOULDER, LEFT_WRIST, ORANGE, "L")
    right_angle = draw_arm(img, points, size, RIGHT_SHOULDER, RIGHT_WRIST, BLUE, "R")

    # The two results, computed by the same functions arm_up.py uses.
    result_a = which_arm_is_up(points, original_size, rule="margin")
    result_b = which_arm_is_up(points, original_size, rule="angle")
    panel = np.full((PANEL, size[0], 3), 255, np.uint8)
    cv2.putText(panel, Path(image_path).name, (12, 28), FONT, 0.65, BLACK, 2, cv2.LINE_AA)
    cv2.putText(panel, f"L {left_angle:+.0f} deg   R {right_angle:+.0f} deg", (12, 56), FONT, 0.55, BLACK, 1, cv2.LINE_AA)
    cv2.putText(panel, f"A (wrist above shoulder): {result_a}", (12, 88), FONT, 0.6, MAGENTA, 2, cv2.LINE_AA)
    cv2.putText(panel, f"B (arm >= {MIN_ANGLE} deg): {result_b}", (12, 116), FONT, 0.6, CYAN, 2, cv2.LINE_AA)
    same = result_a == result_b
    cv2.putText(panel, "same result" if same else "DIFFERENT", (12, 148), FONT, 0.55, GREEN if same else RED, 2, cv2.LINE_AA)
    return np.vstack([img, panel]), result_a, result_b


def rule_sweep():
    """Raise one straight arm from -30 to 90 degrees and show what each rule decides.

    The photos above all give the same result with both rules, because their arms are either
    far above or far below the shoulder. The rules only disagree for arms a little above
    horizontal, which this drawing shows. It uses an arm 0.8 times as long as the torso,
    about the proportion MediaPipe finds in the test photos.
    """
    from types import SimpleNamespace

    from arm_up import is_raised

    width, height, torso, arm = 900, 560, 250, 200
    img = np.full((height, width, 3), 255, np.uint8)
    shoulder_px = (330, 330)
    size = (width, height)

    def landmark(x, y):
        return SimpleNamespace(x=x / width, y=y / height, visibility=1.0)

    shoulder = landmark(*shoulder_px)
    # Only the shoulders and hips matter for the torso length.
    points = {LEFT_SHOULDER: shoulder, RIGHT_SHOULDER: shoulder}
    from arm_up import LEFT_HIP, RIGHT_HIP
    points[LEFT_HIP] = points[RIGHT_HIP] = landmark(shoulder_px[0], shoulder_px[1] + torso)

    cv2.putText(img, "Where the two rules disagree (straight arm, 0.8 x torso long)", (20, 34), FONT, 0.65, BLACK, 2, cv2.LINE_AA)
    cv2.circle(img, shoulder_px, 9, BLACK, -1, cv2.LINE_AA)
    label(img, "shoulder", (shoulder_px[0] - 110, shoulder_px[1] + 30), BLACK, 0.55, 1)

    rows = []
    for angle in (-30, 0, 5, 10, 15, 20, 25, 30, 45, 60, 90):
        rad = math.radians(angle)
        wrist_px = (int(shoulder_px[0] + arm * math.cos(rad)), int(shoulder_px[1] - arm * math.sin(rad)))
        wrist = landmark(*wrist_px)
        a = is_raised(wrist, shoulder, points, size, rule="margin")
        b = is_raised(wrist, shoulder, points, size, rule="angle")
        color = GREEN if a and b else RED if not a and not b else ORANGE
        cv2.line(img, shoulder_px, wrist_px, color, 3, cv2.LINE_AA)
        cv2.circle(img, wrist_px, 5, color, -1, cv2.LINE_AA)
        label(img, f"{angle}", (wrist_px[0] + 8, wrist_px[1] + 5), color, 0.45, 1)
        rows.append((angle, a, b, color))

    # The threshold of each rule, drawn the same way as on the photos.
    a_y = int(shoulder_px[1] - MARGIN * torso)
    dashed_line(img, (shoulder_px[0] - 40, a_y), (shoulder_px[0] + arm + 40, a_y), MAGENTA)
    label(img, "A", (shoulder_px[0] + arm + 46, a_y + 6), MAGENTA)
    rad = math.radians(MIN_ANGLE)
    cv2.line(img, shoulder_px, (int(shoulder_px[0] + 1.25 * arm * math.cos(rad)),
                                int(shoulder_px[1] - 1.25 * arm * math.sin(rad))), CYAN, 2, cv2.LINE_AA)
    label(img, "B", (int(shoulder_px[0] + 1.25 * arm * math.cos(rad)) + 6, int(shoulder_px[1] - 1.25 * arm * math.sin(rad))), CYAN)

    # A small table on the right.
    x0, y0 = 620, 80
    cv2.putText(img, "angle   A     B", (x0, y0), FONT, 0.6, BLACK, 2, cv2.LINE_AA)
    for i, (angle, a, b, color) in enumerate(rows):
        y = y0 + 30 + i * 28
        cv2.putText(img, f"{angle:>4}", (x0, y), FONT, 0.6, color, 2, cv2.LINE_AA)
        cv2.putText(img, "up" if a else "-", (x0 + 85, y), FONT, 0.6, color, 2, cv2.LINE_AA)
        cv2.putText(img, "up" if b else "-", (x0 + 150, y), FONT, 0.6, color, 2, cv2.LINE_AA)
    cv2.putText(img, "green: both up   red: both down   orange: rules disagree", (20, height - 20), FONT, 0.55, BLACK, 1, cv2.LINE_AA)
    return img


def main():
    if len(sys.argv) < 2:
        sys.exit("Usage: python visualize.py <image> [more images...]")
    OUTPUT_DIR.mkdir(exist_ok=True)
    landmarker = create_landmarker()
    pictures = []
    for image_path in sys.argv[1:]:
        picture, result_a, result_b = annotate(image_path, landmarker)
        out = OUTPUT_DIR / f"{Path(image_path).stem}.png"
        cv2.imwrite(str(out), picture)
        pictures.append(picture)
        print(f"{image_path}: A={result_a}, B={result_b} -> {out.name}")

    gap = np.full((pictures[0].shape[0], 12, 3), 255, np.uint8)
    row = [pictures[0]]
    for picture in pictures[1:]:
        row += [gap, picture]
    cv2.imwrite(str(OUTPUT_DIR / "comparison.png"), np.hstack(row))
    cv2.imwrite(str(OUTPUT_DIR / "rules.png"), rule_sweep())
    print("comparison.png and rules.png saved")


if __name__ == "__main__":
    main()
