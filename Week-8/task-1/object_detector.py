"""Object Detector: finds objects in an image and draws a labeled box around each one.

Usage: python object_detector.py [image]   (default: samples/cat_and_dog.jpg)
Model: EfficientDet-Lite0, trained on the 80 COCO classes (person, car, dog, cup...).
Unlike the Image Classifier, it can find several objects and says where each one is.
"""

import cv2
from mediapipe.tasks.python import BaseOptions, vision

from common import GREEN, box_corners, draw_text, input_path, load_image, model, save

path = input_path("cat_and_dog.jpg")
image, drawing = load_image(path)

options = vision.ObjectDetectorOptions(
    base_options=BaseOptions(model_asset_path=model("efficientdet_lite0.tflite")),
    score_threshold=0.4,  # Ignore guesses the model is less than 40% sure about.
)
with vision.ObjectDetector.create_from_options(options) as detector:
    result = detector.detect(image)

print(f"{path.name}: {len(result.detections)} object(s)")
for detection in result.detections:
    box = detection.bounding_box
    category = detection.categories[0]
    print(f"  {category.category_name} {category.score:.0%} at x={box.origin_x} y={box.origin_y} {box.width}x{box.height}")
    top_left, bottom_right = box_corners(box, image, drawing)
    cv2.rectangle(drawing, top_left, bottom_right, GREEN, 3)
    draw_text(drawing, f"{category.category_name} {category.score:.0%}", (top_left[0] + 6, top_left[1] + 30), GREEN, 0.9)

save(drawing, "object_detector.png")
