"""The three models behind AI Art Chat, each wrapped in a small class.

- ImageGenerator: Stable Diffusion Turbo turns a text prompt into a 512x512 image in one step.
- Chatbot: SmolLM2-360M-Instruct answers chat messages.
- SpeechToText: Whisper small turns a voice recording into text.

All of them run locally on the Mac GPU (MPS) when there is one, otherwise on the CPU.
"""

import base64
import io
import os
import warnings

# Use only the downloaded models (download_models.py); never wait on the internet.
os.environ.setdefault("HF_HUB_OFFLINE", "1")
warnings.filterwarnings("ignore")

import torch  # noqa: E402
from diffusers import AutoPipelineForText2Image  # noqa: E402
from transformers import pipeline  # noqa: E402
from transformers.utils import logging  # noqa: E402

logging.set_verbosity_error()

DEVICE = "mps" if torch.backends.mps.is_available() else "cpu"


class ImageGenerator:
    """Text to image with Stable Diffusion Turbo, a version of Stable Diffusion 2.1 distilled to
    give a good image in a single denoising step instead of 25-50."""

    MODEL = "stabilityai/sd-turbo"

    def __init__(self):
        self.pipe = AutoPipelineForText2Image.from_pretrained(
            self.MODEL, variant="fp16", torch_dtype=torch.float16).to(DEVICE)
        # float16 halves the memory and makes an image in about 3 s on an M2 (float32: about 9 s).
        self.pipe.set_progress_bar_config(disable=True)

    def generate(self, prompt):
        """Return the image as a base64 PNG string, ready for an <img src="data:..."> tag."""
        # Turbo models are trained for 1 step and no classifier-free guidance (guidance_scale=0).
        image = self.pipe(prompt=prompt, num_inference_steps=1, guidance_scale=0.0).images[0]
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode()


class Chatbot:
    """A small chat model. It sees the last few messages of the conversation, so it can follow up."""

    MODEL = "HuggingFaceTB/SmolLM2-360M-Instruct"
    SYSTEM = ("You are a friendly assistant inside AI Art Chat, an app that paints images from text "
              "prompts. Keep your answers short: one to three sentences. When the user asks for an "
              "image prompt, answer with a single vivid description of the scene, its colors, "
              "lighting and style, without any introduction.")
    HISTORY = 6  # how many earlier messages the model sees; a 360M model loses track of long chats

    def __init__(self):
        self.pipe = pipeline("text-generation", model=self.MODEL, device=DEVICE)

    def reply(self, messages):
        """messages: [{"role": "user" | "assistant", "content": "..."}, ...], the last one from the user."""
        chat = [{"role": "system", "content": self.SYSTEM}] + messages[-self.HISTORY:]
        # The pipeline applies the model's chat template and returns the chat with the new answer.
        result = self.pipe(chat, max_new_tokens=120, do_sample=True, temperature=0.4, top_p=0.9)
        return result[0]["generated_text"][-1]["content"].strip()


class SpeechToText:
    """Speech recognition with Whisper small (244M parameters, about 1 GB in float32).

    Whisper large-v3 was tried first: on the Mac GPU it only works in float32 (float16 and
    bfloat16 give garbage like "!"), which takes about 6 GB, and next to the other two models it
    pushed a 16 GB Mac into swap. Whisper small transcribes clear English just as well in ~2 s.
    """

    MODEL = "openai/whisper-small"

    def __init__(self):
        self.pipe = pipeline("automatic-speech-recognition", model=self.MODEL,
                             dtype=torch.float32, device=DEVICE)

    def transcribe(self, audio_bytes):
        """audio_bytes: a recording from the browser (webm or mp4); ffmpeg decodes it."""
        result = self.pipe(audio_bytes, generate_kwargs={"language": "english", "task": "transcribe"})
        return result["text"].strip()
