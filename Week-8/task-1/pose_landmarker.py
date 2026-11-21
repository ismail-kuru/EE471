"""Pose Landmarker: finds 33 points on the body (face, shoulders, elbows, wrists, hips, knees, feet).

Usage: python pose_landmarker.py [image]   (default: samples/pose-1.jpg)
Model: a person detector followed by a pose landmark model. Each point has x and y (0-1), a depth z
and a visibility score. Task 2 uses this model to find which arm is raised.
"""

from mediapipe.tasks.python import BaseOptions, vision

from common import GREEN, draw_landmarks, input_path, load_image, model, save

path = input_path("pose-1.jpg")
image, drawing = load_image(path)

options = vision.PoseLandmarkerOptions(base_options=BaseOptions(model_asset_path=model("pose_landmarker_full.task")))
with vision.PoseLandmarker.create_from_options(options) as landmarker:
    result = landmarker.detect(image)

if not result.pose_landmarks:
    raise SystemExit(f"{path.name}: no person found")

points = result.pose_landmarks[0]
draw_landmarks(drawing, points, vision.PoseLandmarksConnections.POSE_LANDMARKS, GREEN, 4)
print(f"{path.name}: {len(points)} body points")
for name, index in (("nose", 0), ("left wrist", 15), ("right wrist", 16), ("left ankle", 27), ("right ankle", 28)):
    p = points[index]
    print(f"  {name:12} x={p.x:.2f} y={p.y:.2f} visibility={p.visibility:.2f}")

save(drawing, "pose_landmarker.png")
