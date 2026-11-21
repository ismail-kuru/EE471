"""Face Detector: finds faces in an image and draws a box around each one.

Usage: python face_detector.py [image]   (default: samples/face-3.png)
Model: BlazeFace (short range), made for faces within about 2 m of the camera. Besides the box,
it returns 6 key points: both eyes, the nose tip, the mouth and both ear areas.
"""

import cv2
from mediapipe.tasks.python import BaseOptions, vision

from common import GREEN, YELLOW, box_corners, draw_text, input_path, load_image, model, pixel, save

path = input_path("face-3.png")
image, drawing = load_image(path)

options = vision.FaceDetectorOptions(base_options=BaseOptions(model_asset_path=model("blaze_face_short_range.tflite")))
with vision.FaceDetector.create_from_options(options) as detector:
    result = detector.detect(image)

print(f"{path.name}: {len(result.detections)} face(s)")
for detection in result.detections:
    box = detection.bounding_box
    score = detection.categories[0].score
    print(f"  box x={box.origin_x} y={box.origin_y} {box.width}x{box.height}, score {score:.0%}")
    top_left, bottom_right = box_corners(box, image, drawing)
    cv2.rectangle(drawing, top_left, bottom_right, GREEN, 3)
    for point in detection.keypoints:  # Eyes, nose tip, mouth and ear areas.
        cv2.circle(drawing, pixel(point, drawing), 7, YELLOW, -1)
    draw_text(drawing, f"face {score:.0%}", (top_left[0], max(top_left[1] - 10, 24)), GREEN, 0.9)

save(drawing, "face_detector.png")
