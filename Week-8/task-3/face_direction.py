"""Find which way a face in a photo is looking.

Usage: python face_direction.py images/face-1.png [more images...]
Output for each image: "left", "right" or "straight".
"Left" and "right" are the person's own sides: a person who turns their head to their
left is looking towards the right side of the photo.
"""

import math
import os
import sys
from pathlib import Path

import mediapipe as mp
import numpy as np
from mediapipe.tasks.python import BaseOptions, vision

DEFAULT_MODEL = Path(__file__).resolve().parent / "models" / "face_landmarker.task"
MODEL_PATH = Path(os.environ.get("FACE_MODEL", DEFAULT_MODEL))

# A head turned less than this many degrees counts as looking straight.
YAW_THRESHOLD = 15


def create_landmarker(model_path=MODEL_PATH):
    """Load the face model once; it can then be used for many images."""
    options = vision.FaceLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=str(model_path)),
        # Also return the head's rotation, as a 4x4 transformation matrix.
        output_facial_transformation_matrixes=True,
        num_faces=1,
    )
    return vision.FaceLandmarker.create_from_options(options)


def head_yaw(matrix):
    """Return how far the head is turned sideways, in degrees.

    The top-left 3x3 part of the matrix is the head's rotation. Negative means the person
    turned to their right, positive to their left.
    """
    rotation = np.array(matrix)[:3, :3]
    return math.degrees(math.atan2(-rotation[2, 0], math.hypot(rotation[0, 0], rotation[1, 0])))


def direction_from_yaw(yaw):
    """Turn the yaw angle into "left", "right" or "straight"."""
    if yaw < -YAW_THRESHOLD:
        return "right"
    if yaw > YAW_THRESHOLD:
        return "left"
    return "straight"


def classify(image_path, landmarker):
    """Detect the face in the image and say which way it is looking."""
    result = landmarker.detect(mp.Image.create_from_file(str(image_path)))
    if not result.facial_transformation_matrixes:
        raise ValueError(f"No face found in {image_path}")
    return direction_from_yaw(head_yaw(result.facial_transformation_matrixes[0]))


def main():
    if len(sys.argv) < 2:
        sys.exit("Usage: python face_direction.py <image> [more images...]")
    landmarker = create_landmarker()
    for image_path in sys.argv[1:]:
        print(f"{image_path}: {classify(image_path, landmarker)}")


if __name__ == "__main__":
    main()
