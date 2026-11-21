"""Gesture Recognizer: recognizes hand gestures such as thumbs up, victory or a closed fist.

Usage: python gesture_recognizer.py [image ...]   (default: the three gesture samples)
Model: hand landmarker + a gesture classifier with 7 gestures: Closed_Fist, Open_Palm,
Pointing_Up, Thumb_Down, Thumb_Up, Victory and ILoveYou ("None" if no gesture matches).
"""

import sys

from mediapipe.tasks.python import BaseOptions, vision

from common import GREEN, SAMPLES, draw_landmarks, draw_text, load_image, model, save

paths = sys.argv[1:] or [SAMPLES / name for name in ("thumbs_up.jpg", "victory.jpg", "pointing_up.jpg")]

options = vision.GestureRecognizerOptions(base_options=BaseOptions(model_asset_path=model("gesture_recognizer.task")))
with vision.GestureRecognizer.create_from_options(options) as recognizer:
    for path in paths:
        image, drawing = load_image(path)
        result = recognizer.recognize(image)
        if not result.gestures:
            print(f"{path}: no hand found")
            continue
        gesture = result.gestures[0][0]
        hand = result.handedness[0][0].category_name
        print(f"{path}: {gesture.category_name} ({gesture.score:.0%}), {hand} hand")
        draw_landmarks(drawing, result.hand_landmarks[0], vision.HandLandmarksConnections.HAND_CONNECTIONS, GREEN, 4)
        draw_text(drawing, f"{gesture.category_name} {gesture.score:.0%}", (14, 44), GREEN, 1.2)
        # Same model for every image; one output picture per input image.
        save(drawing, f"gesture_recognizer_{str(path).rsplit('/', 1)[-1].rsplit('.', 1)[0]}.png")
