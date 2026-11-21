"""Image Segmenter: labels every pixel of an image with a class (person, cat, dog, background...).

Usage: python image_segmenter.py [image]   (default: samples/cat_and_dog.jpg)
Model: DeepLab-V3, with 21 classes. The result is a mask the size of the image, holding the class
number of each pixel; here each class gets a color laid over the photo.
"""

import cv2
import numpy as np
from mediapipe.tasks.python import BaseOptions, vision

from common import add_panel, input_path, load_image, model, save

path = input_path("cat_and_dog.jpg")
image, drawing = load_image(path)

options = vision.ImageSegmenterOptions(
    base_options=BaseOptions(model_asset_path=model("deeplab_v3.tflite")),
    output_category_mask=True,
)
with vision.ImageSegmenter.create_from_options(options) as segmenter:
    result = segmenter.segment(image)
    labels = segmenter.labels

# One class number per pixel (0 is background). MediaPipe returns it as height x width x 1.
mask = result.category_mask.numpy_view().squeeze()
# The drawing may be enlarged, so stretch the mask to its size (nearest keeps whole class numbers).
mask_drawing = cv2.resize(mask, (drawing.shape[1], drawing.shape[0]), interpolation=cv2.INTER_NEAREST)
colors = np.random.default_rng(1).integers(60, 255, size=(len(labels), 3), dtype=np.uint8)
colors[0] = 0
overlay = colors[mask_drawing]
drawing = np.where(mask_drawing[..., None] > 0, cv2.addWeighted(drawing, 0.4, overlay, 0.6, 0), drawing)

lines = []
for class_id in (c for c in np.unique(mask) if c != 0):
    lines.append(f"{labels[class_id]}: {(mask == class_id).mean():.0%} of the image")
print(f"{path.name}:")
for line in lines:
    print(f"  {line}")

save(add_panel(drawing, ["Classes found:"] + lines), "image_segmenter.png")
