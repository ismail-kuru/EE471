"""Universal Embedder: turns texts AND images into vectors in the same space, so they can be compared.

Usage: python universal_embedder.py
Model: EmbeddingGemma 2 (440M, text and vision). Unlike the Text Embedder and Image Embedder, a
sentence and a photo can be compared directly: "a photo of a cat" should be closest to the cat photo.
"""

from mediapipe.tasks.python import BaseOptions, retrieval

from common import SAMPLES, model

texts = ["a photo of a cat", "a hand showing a thumbs up", "a woman raising her arm"]
images = ["cat.jpg", "thumbs_up.jpg", "pose-1.jpg"]

options = retrieval.UniversalEmbedderOptions(
    base_options=BaseOptions(model_asset_path=model("embeddinggemma-2-text-vision-440m.litertlm")),
    l2_normalize=True,
)
with retrieval.UniversalEmbedder.create_from_options(options) as embedder:
    text_vectors = [embedder.embed_text(t).embeddings[0] for t in texts]
    image_vectors = [embedder.embed_image((SAMPLES / name).read_bytes()).embeddings[0] for name in images]

print(f"Each text or image becomes {len(text_vectors[0].embedding)} numbers.")
print("Cosine similarity, text (rows) vs image (columns):")
print(" " * 30 + "".join(f"{name:>16}" for name in images))
for text, t_vec in zip(texts, text_vectors):
    row = [retrieval.UniversalEmbedder.cosine_similarity(t_vec, i_vec) for i_vec in image_vectors]
    best = images[row.index(max(row))]
    print(f"{text:30}" + "".join(f"{s:16.2f}" for s in row) + f"   -> {best}")
