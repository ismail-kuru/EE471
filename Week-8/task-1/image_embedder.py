"""Image Embedder: turns an image into a list of numbers (an embedding) so images can be compared.

Usage: python image_embedder.py [image ...]   (default: three sample images)
Model: MobileNet-V3 (small). Similar-looking images get similar vectors; the cosine similarity
is close to 1 for alike images and lower for different ones.
"""

import sys
from itertools import combinations

from mediapipe.tasks.python import BaseOptions, vision

from common import SAMPLES, load_image, model

paths = sys.argv[1:] or [SAMPLES / name for name in ("cat.jpg", "cat_and_dog.jpg", "thumbs_up.jpg")]

options = vision.ImageEmbedderOptions(base_options=BaseOptions(model_asset_path=model("mobilenet_v3_small.tflite")), l2_normalize=True)
with vision.ImageEmbedder.create_from_options(options) as embedder:
    embeddings = [embedder.embed(load_image(p)[0]).embeddings[0] for p in paths]

print(f"Each image becomes {len(embeddings[0].embedding)} numbers.")
for (i, a), (j, b) in combinations(enumerate(embeddings), 2):
    similarity = vision.ImageEmbedder.cosine_similarity(a, b)
    print(f"{similarity:.2f}  {str(paths[i]).rsplit('/', 1)[-1]} vs {str(paths[j]).rsplit('/', 1)[-1]}")
