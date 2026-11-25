"""The inputs of the Week 9 exercise, shared by the module's self-test and the Gradio demo."""

from pathlib import Path

SAMPLES = Path(__file__).resolve().parent.parent / "samples"
IMAGE = str(SAMPLES / "pipeline-cat-chonk.jpeg")
AUDIO = str(SAMPLES / "mlk.flac")

SENTIMENT = ["I've been waiting for a modern software practices course my whole life.", "I hate software courses"]
ZERO_SHOT = "Berkshire keeps their cash reserves at an extremely high level."
ZERO_SHOT_LABELS = ["finance", "education", "politics", "sports", "technology"]
GENERATION = "If I continue to complete all in-class exercises in this modern software practices course,"
FILL_MASK = "To understand generative AI, one must study […] well."
NATE = ("I am Nate, a research assistant at Izmir Institute of Technology, and currently living and "
        "working in the beautiful city İzmir in Türkiye.")
QUESTIONS = ["What is my name?", "Where do I work?", "In which city do I live?"]
CRISIS_TEXT = (
    "The 2008 Global Financial Crisis stands as the most severe economic collapse of the 21st century, "
    "often compared to the Great Depression of the 1930s. Triggered by the bursting of the United States "
    "housing bubble, its effects rippled across the globe, leading to the collapse of major financial "
    "institutions and a deep international recession. The crisis began with the subprime mortgage market. "
    "In the early 2000s, low interest rates and a push for homeownership led banks to issue high-risk loans "
    "to borrowers with poor credit."
)
TRANSLATION = "Ce cours est produit par Hugging Face."  # French
