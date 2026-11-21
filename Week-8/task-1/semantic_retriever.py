"""Semantic Retriever: stores texts and finds the ones that answer a question by meaning, not by words.

Usage: python semantic_retriever.py ["a question"]   (default: three example questions)
Model: EmbeddingGemma 2 (440M) through the Universal Embedder. Each text is turned into a vector and
kept in a small database; a question is turned into a vector too, and the closest texts come back.
This is the "retrieval" step of RAG, where an assistant looks up facts before answering.
"""

import sys

from mediapipe.tasks.python import BaseOptions, retrieval

from common import model

documents = {
    "docker": "Docker packages an application with everything it needs, so it runs the same on every computer.",
    "cog": "Cog builds a Docker image for a machine learning model and serves it behind an HTTP API.",
    "pose": "MediaPipe's pose landmarker finds 33 points on the human body, such as shoulders and wrists.",
    "iyte": "Izmir Institute of Technology is a university in Urla, near the city of Izmir in Turkey.",
    "pizza": "A Margherita pizza is topped with tomato sauce, mozzarella and fresh basil.",
}
questions = sys.argv[1:] or [
    "How can I run a model as a web service?",
    "Which tool finds where someone's arms are?",
    "Where is IYTE located?",
]

embedder_options = retrieval.UniversalEmbedderOptions(
    base_options=BaseOptions(model_asset_path=model("embeddinggemma-2-text-vision-440m.litertlm")),
    l2_normalize=True,
)
with retrieval.UniversalEmbedder.create_from_options(embedder_options) as embedder:
    # The database lives in memory; embedding_dimension must match the model's vectors (768).
    retriever_options = retrieval.SemanticRetrieverOptions(embedder=embedder, embedding_dimension=768)
    with retrieval.SemanticRetriever.create_from_options(retriever_options) as retriever:
        for doc_id, text in documents.items():
            retriever.insert_document(doc_id=doc_id, text=text)
        print(f"Stored {len(documents)} texts.")
        for question in questions:
            print(f"\nQ: {question}")
            for hit in retriever.retrieve(query=question, limit=2):
                print(f"  {hit.score:.2f}  {hit.content}")
