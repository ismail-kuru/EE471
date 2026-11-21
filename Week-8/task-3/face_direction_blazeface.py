"""The same task as face_direction.py, solved with the simpler Face Detector (BlazeFace) for comparison.

Usage: python face_direction_blazeface.py images/face-1.png [more images...]
Output for each image: "left", "right" or "straight" (the person's own sides, as in face_direction.py).

BlazeFace returns only a box and 6 points (both eyes, nose tip, mouth, both ears), not the head's
rotation. So the direction comes from geometry: when the head turns, the nose tip moves sideways
from the middle of the eyes. Not used by Cog; face_direction.py is the real solution.
"""

import sys
from pathlib import Path

import mediapipe as mp
from mediapipe.tasks.python import BaseOptions, vision

MODEL_PATH = Path(__file__).resolve().parent / "models" / "blaze_face_short_range.tflite"

# Order of BlazeFace's 6 key points. Right and left are the person's own sides.
RIGHT_EYE, LEFT_EYE, NOSE_TIP = 0, 1, 2

# A nose shifted by less than this share of the eye distance counts as looking straight.
OFFSET_THRESHOLD = 0.2


def create_detector(model_path=MODEL_PATH):
    """Load the face detector once; it can then be used for many images."""
    options = vision.FaceDetectorOptions(base_options=BaseOptions(model_asset_path=str(model_path)))
    return vision.FaceDetector.create_from_options(options)


def nose_offset(keypoints):
    """How far the nose tip is from the middle of the eyes, in eye distances.

    Points are in 0-1 image units; dividing by the eye distance makes the value the same for
    big and small faces. Negative means the nose moved to the photo's left side.
    """
    right_eye, left_eye, nose = keypoints[RIGHT_EYE], keypoints[LEFT_EYE], keypoints[NOSE_TIP]
    eyes_middle = (right_eye.x + left_eye.x) / 2
    eye_distance = abs(left_eye.x - right_eye.x)
    return (nose.x - eyes_middle) / eye_distance


def direction_from_offset(offset):
    """A nose on the photo's left means the person turned to their own right."""
    if offset < -OFFSET_THRESHOLD:
        return "right"
    if offset > OFFSET_THRESHOLD:
        return "left"
    return "straight"


def classify(image_path, detector):
    """Detect the face and say which way it is looking."""
    result = detector.detect(mp.Image.create_from_file(str(image_path)))
    if not result.detections:
        raise ValueError(f"No face found in {image_path}")
    return direction_from_offset(nose_offset(result.detections[0].keypoints))


def main():
    if len(sys.argv) < 2:
        sys.exit("Usage: python face_direction_blazeface.py <image> [more images...]")
    detector = create_detector()
    for image_path in sys.argv[1:]:
        result = detector.detect(mp.Image.create_from_file(str(image_path)))
        if not result.detections:
            print(f"{image_path}: no face found")
            continue
        offset = nose_offset(result.detections[0].keypoints)
        print(f"{image_path}: {direction_from_offset(offset)} (nose offset {offset:+.2f})")


if __name__ == "__main__":
    main()
