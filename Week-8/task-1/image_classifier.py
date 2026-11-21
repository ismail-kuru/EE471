"""Image Classifier: says what the main object in an image is, out of 1000 ImageNet classes.

Usage: python image_classifier.py [image]   (default: samples/cat.jpg)
Model: EfficientNet-Lite0. It gives one answer for the whole image, not a box per object
(that is the Object Detector).
"""

from mediapipe.tasks.python import BaseOptions, vision

from common import add_panel, input_path, load_image, model, save

path = input_path("cat.jpg")
image, drawing = load_image(path)

options = vision.ImageClassifierOptions(base_options=BaseOptions(model_asset_path=model("efficientnet_lite0.tflite")), max_results=5)
with vision.ImageClassifier.create_from_options(options) as classifier:
    result = classifier.classify(image)

lines = [f"{c.category_name}: {c.score:.0%}" for c in result.classifications[0].categories]
print(f"{path.name}:")
for line in lines:
    print(f"  {line}")

save(add_panel(drawing, ["Top 5 classes:"] + lines), "image_classifier.png")
