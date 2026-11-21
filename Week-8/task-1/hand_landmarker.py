"""Hand Landmarker: finds 21 points on each hand (wrist, knuckles, finger tips) and says left or right.

Usage: python hand_landmarker.py [image]   (default: samples/woman_hands.jpg)
Model: a palm detector followed by a hand landmark model; up to num_hands hands.
"""

from mediapipe.tasks.python import BaseOptions, vision

from common import BLUE, GREEN, draw_landmarks, draw_text, input_path, load_image, model, pixel, save

path = input_path("woman_hands.jpg")
image, drawing = load_image(path)

options = vision.HandLandmarkerOptions(base_options=BaseOptions(model_asset_path=model("hand_landmarker.task")), num_hands=2)
with vision.HandLandmarker.create_from_options(options) as landmarker:
    result = landmarker.detect(image)

print(f"{path.name}: {len(result.hand_landmarks)} hand(s)")
for points, handedness in zip(result.hand_landmarks, result.handedness):
    side = handedness[0].category_name
    color = GREEN if side == "Left" else BLUE
    draw_landmarks(drawing, points, vision.HandLandmarksConnections.HAND_CONNECTIONS, color, 5)
    wrist = pixel(points[0], drawing)
    draw_text(drawing, f"{side} {handedness[0].score:.0%}", (wrist[0] - 30, wrist[1] + 30), color, 0.8)
    print(f"  {side} hand ({handedness[0].score:.0%}), index finger tip at {pixel(points[8], drawing)}")

save(drawing, "hand_landmarker.png")
