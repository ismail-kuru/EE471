"""Download the three models of the app into the Hugging Face cache (~/.cache/huggingface/hub).

Run: python download_models.py (about 3.4 GB in total)
"""

from huggingface_hub import snapshot_download

# Stable Diffusion Turbo: one copy of the float16 weights (about 2.5 GB), not the float32 ones.
snapshot_download("stabilityai/sd-turbo", allow_patterns=["*.json", "*.txt", "*fp16.safetensors"])
# The chatbot (about 0.7 GB).
snapshot_download("HuggingFaceTB/SmolLM2-360M-Instruct",
                  allow_patterns=["*.json", "*.txt", "*.safetensors"])
# Speech to text (about 1 GB).
snapshot_download("openai/whisper-small",
                  allow_patterns=["*.json", "*.txt", "model.safetensors"])
print("All models downloaded.")
