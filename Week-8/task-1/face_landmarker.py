"""Face Landmarker: finds 478 points on a face, plus facial expressions (blendshapes).

Usage: python face_landmarker.py [image]   (default: samples/face-3.png)
Model: face detector + face mesh + blendshapes. The blendshapes are 52 scores between 0 and 1,
such as how much the person smiles or how open each eye is.
"""

from mediapipe.tasks.python import BaseOptions, vision

from common import GREEN, add_panel, draw_landmarks, input_path, load_image, model, save

path = input_path("face-3.png")
image, drawing = load_image(path)

options = vision.FaceLandmarkerOptions(
    base_options=BaseOptions(model_asset_path=model("face_landmarker.task")),
    output_face_blendshapes=True,
    num_faces=1,
)
with vision.FaceLandmarker.create_from_options(options) as landmarker:
    result = landmarker.detect(image)

if not result.face_landmarks:
    raise SystemExit(f"{path.name}: no face found")

points = result.face_landmarks[0]
print(f"{path.name}: {len(points)} face points")
# The face outline, eyes, eyebrows and lips, drawn from the model's own connection list.
draw_landmarks(drawing, points, vision.FaceLandmarksConnections.FACE_LANDMARKS_CONTOURS, GREEN, radius=2)

top = sorted(result.face_blendshapes[0], key=lambda b: b.score, reverse=True)[:5]
lines = [f"{b.category_name}: {b.score:.2f}" for b in top]
print("Strongest expressions:")
for line in lines:
    print(f"  {line}")

save(add_panel(drawing, ["Strongest expressions (0-1):"] + lines), "face_landmarker.png")
