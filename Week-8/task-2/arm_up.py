"""Find which arm is raised in a photo of a person.

Usage: python arm_up.py images/pose-1.jpg [more images...]
Output for each image: "left", "right", "both" or "None".
"Left" and "right" are the person's own arms, as MediaPipe names them.
"""

import math
import os
import sys
from pathlib import Path

import mediapipe as mp
from mediapipe.tasks.python import BaseOptions, vision

DEFAULT_MODEL = Path(__file__).resolve().parent / "models" / "pose_landmarker_full.task"
MODEL_PATH = Path(os.environ.get("POSE_MODEL", DEFAULT_MODEL))

# Indexes of the body points (landmarks) MediaPipe's pose model returns.
LEFT_SHOULDER, RIGHT_SHOULDER = 11, 12
LEFT_WRIST, RIGHT_WRIST = 15, 16
LEFT_HIP, RIGHT_HIP = 23, 24

# A point is only trusted if the model is at least this sure it is visible.
MIN_VISIBILITY = 0.5

# Two ways to decide if an arm is raised (see visualize.py for a comparison):
#   "margin": the wrist is above the shoulder by MARGIN times the torso length,
#             so a fist held at shoulder height does not count.
#   "angle":  the line from shoulder to wrist points at least MIN_ANGLE degrees above horizontal.
RULE = "margin"  # The rule in use. Change to "angle" to use rule B.
MARGIN = 0.15
MIN_ANGLE = 20


def create_landmarker(model_path=MODEL_PATH):
    """Load the pose model once; it can then be used for many images."""
    options = vision.PoseLandmarkerOptions(base_options=BaseOptions(model_asset_path=str(model_path)))
    return vision.PoseLandmarker.create_from_options(options)


def torso_length(points):
    """Distance from the shoulders to the hips, in the image's 0-1 height units."""
    shoulder_y = (points[LEFT_SHOULDER].y + points[RIGHT_SHOULDER].y) / 2
    hip_y = (points[LEFT_HIP].y + points[RIGHT_HIP].y) / 2
    return abs(hip_y - shoulder_y)


def arm_angle(wrist, shoulder, image_size):
    """Angle of the shoulder-to-wrist line above the horizontal, in degrees (negative = below).

    Landmarks are scaled to 0-1 separately in width and height, so they are turned back
    into pixels first; otherwise the angle would be stretched in tall images.
    """
    width, height = image_size
    across = abs(wrist.x - shoulder.x) * width
    up = (shoulder.y - wrist.y) * height  # Image y grows downwards, so up means a smaller y.
    return math.degrees(math.atan2(up, across))


def is_raised(wrist, shoulder, points, image_size, rule=RULE):
    """True if this arm counts as raised under the chosen rule."""
    if wrist.visibility < MIN_VISIBILITY or shoulder.visibility < MIN_VISIBILITY:
        return False
    if rule == "angle":
        return arm_angle(wrist, shoulder, image_size) >= MIN_ANGLE
    return shoulder.y - wrist.y > MARGIN * torso_length(points)


def which_arm_is_up(points, image_size, rule=RULE):
    """Turn one person's landmarks into "left", "right", "both" or "None"."""
    left = is_raised(points[LEFT_WRIST], points[LEFT_SHOULDER], points, image_size, rule)
    right = is_raised(points[RIGHT_WRIST], points[RIGHT_SHOULDER], points, image_size, rule)
    if left and right:
        return "both"
    if left:
        return "left"
    if right:
        return "right"
    return "None"


def classify(image_path, landmarker):
    """Detect the person in the image and say which arm is up."""
    image = mp.Image.create_from_file(str(image_path))
    result = landmarker.detect(image)
    if not result.pose_landmarks:  # No person found.
        return "None"
    return which_arm_is_up(result.pose_landmarks[0], (image.width, image.height))


def main():
    if len(sys.argv) < 2:
        sys.exit("Usage: python arm_up.py <image> [more images...]")
    landmarker = create_landmarker()
    for image_path in sys.argv[1:]:
        print(f"{image_path}: {classify(image_path, landmarker)}")


if __name__ == "__main__":
    main()
