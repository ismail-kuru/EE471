"""Interactive Segmenter: cuts out the object under a point the user picks.

Usage: python interactive_segmenter.py [image x y]   (default: samples/cat_and_dog.jpg, a point on the dog)
x and y are between 0 and 1 (0.5 0.5 = the middle of the image).
Model: MagicTouch. Unlike the Image Segmenter it has no class list: it separates whatever is
under the point from everything else.
"""

import sys

import cv2
import numpy as np
from mediapipe.tasks.python import BaseOptions, vision
from mediapipe.tasks.python.vision.interactive_segmenter import BrushMode, Stroke, StrokePoint

from common import GREEN, RED, SAMPLES, load_image, model, save

if len(sys.argv) == 4:
    path, x, y = sys.argv[1], float(sys.argv[2]), float(sys.argv[3])
else:
    path, x, y = SAMPLES / "cat_and_dog.jpg", 0.75, 0.5
image, drawing = load_image(path)

options = vision.InteractiveSegmenterOptions(base_options=BaseOptions(model_asset_path=model("interactive_segmentation.task")))
# The user's input is a "stroke": here a single point, with a POSITIVE brush ("include this").
stroke = Stroke(brush_mode=BrushMode.POSITIVE, points=[StrokePoint(x, y)], is_completed=True)
with vision.InteractiveSegmenter.create_from_options(options) as segmenter:
    segmenter.set_image(image)
    result = segmenter.segment([stroke])

# The result is a mask image the size of the photo; squeeze() drops its last dimension (height x width x 1).
values = result.numpy_view().squeeze()
mask = values > (0.5 if values.dtype.kind == "f" else 0)
height, width = mask.shape
if not mask[int(y * height), int(x * width)]:  # Make sure the object under the point is the "selected" part.
    mask = ~mask

# The drawing may be enlarged, so stretch the mask to its size.
mask_drawing = cv2.resize(mask.astype(np.uint8), (drawing.shape[1], drawing.shape[0]), interpolation=cv2.INTER_NEAREST) > 0
green = np.zeros_like(drawing)
green[:] = GREEN
drawing = np.where(mask_drawing[..., None], cv2.addWeighted(drawing, 0.5, green, 0.5, 0), drawing)
cv2.circle(drawing, (int(x * drawing.shape[1]), int(y * drawing.shape[0])), 12, RED, -1)
print(f"{path}: point ({x}, {y}) -> selected {mask.mean():.0%} of the image")
save(drawing, "interactive_segmenter.png")
