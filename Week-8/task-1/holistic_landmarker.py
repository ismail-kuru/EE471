"""Holistic Landmarker: finds the body pose, the face and both hands of a person in one pass.

Usage: python holistic_landmarker.py [image]   (default: samples/pose-1.jpg)
Model: one bundle that combines the pose (33 points), face (478 points) and hand (21 points per
hand) models, so a single call returns all of them for the same person.
"""

from mediapipe.tasks.python import BaseOptions, vision

from common import BLUE, GREEN, YELLOW, add_panel, draw_landmarks, input_path, load_image, model, save

path = input_path("pose-1.jpg")
image, drawing = load_image(path)

options = vision.HolisticLandmarkerOptions(base_options=BaseOptions(model_asset_path=model("holistic_landmarker.task")))
with vision.HolisticLandmarker.create_from_options(options) as landmarker:
    result = landmarker.detect(image)

# Each part is drawn with its own color, using MediaPipe's own connection lists.
parts = [
    ("pose", result.pose_landmarks, vision.PoseLandmarksConnections.POSE_LANDMARKS, YELLOW, 5),
    ("face", result.face_landmarks, vision.FaceLandmarksConnections.FACE_LANDMARKS_CONTOURS, GREEN, 1),
    ("left hand", result.left_hand_landmarks, vision.HandLandmarksConnections.HAND_CONNECTIONS, BLUE, 4),
    ("right hand", result.right_hand_landmarks, vision.HandLandmarksConnections.HAND_CONNECTIONS, BLUE, 4),
]
lines = []
for name, points, connections, color, radius in parts:
    if points:
        draw_landmarks(drawing, points, connections, color, radius)
    lines.append(f"{name}: {len(points) if points else 0} points")

print(f"{path.name}:")
for line in lines:
    print(f"  {line}")
save(add_panel(drawing, ["One call, four parts:"] + lines), "holistic_landmarker.png")
