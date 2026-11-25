"""Task 1.9: classify an image with Google's ViT. Usage: python image_classification.py [image]"""

from common import input_path, show, title
from transformers import pipeline

image = input_path("pipeline-cat-chonk.jpeg")
classifier = pipeline("image-classification", model="google/vit-base-patch16-224", top_k=5)

title("Image classification (google/vit-base-patch16-224)")
show("Image", image.name)
for result in classifier(str(image)):  # the 5 most likely of the 1000 ImageNet classes
    show(f"{result['score']:.4f}", result["label"])
