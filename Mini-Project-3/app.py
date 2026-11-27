"""AI Art Chat: a web app that paints images from prompts and chats with you by voice or text.

Run: python app.py, then open http://127.0.0.1:5002
The three models are loaded once when the server starts (about 10 s), then every request
reuses them.
"""

import time

from flask import Flask, jsonify, render_template, request

from models import Chatbot, ImageGenerator, SpeechToText

app = Flask(__name__)


def load(name, cls):
    start = time.time()
    model = cls()
    print(f"  {name:<15} ready in {time.time() - start:4.1f} s", flush=True)
    return model


print("Loading models...", flush=True)
image_generator = load("Stable Diffusion", ImageGenerator)
chatbot = load("Chatbot", Chatbot)
speech_to_text = load("Whisper", SpeechToText)
# The first image on the Mac GPU takes ~10 s while it prepares; do it now, not on the first click.
image_generator.generate("warm up")
print("  warmed up", flush=True)


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/api/image")
def generate_image():
    """{"prompt": "..."} -> {"image": "<base64 PNG>"}"""
    prompt = (request.get_json(silent=True) or {}).get("prompt", "").strip()
    if not prompt:
        return jsonify(error="Write a prompt first."), 400
    return jsonify(image=image_generator.generate(prompt))


@app.post("/api/transcribe")
def transcribe():
    """A form with the recording in "audio" -> {"text": "..."}"""
    audio = request.files.get("audio")
    if audio is None:
        return jsonify(error="No recording received."), 400
    return jsonify(text=speech_to_text.transcribe(audio.read()))


@app.post("/api/chat")
def chat():
    """{"messages": [{"role": "user", "content": "..."}, ...]} -> {"reply": "..."}"""
    messages = (request.get_json(silent=True) or {}).get("messages", [])
    if not messages or messages[-1].get("role") != "user":
        return jsonify(error="Send a message first."), 400
    return jsonify(reply=chatbot.reply(messages))


if __name__ == "__main__":
    print("Open http://127.0.0.1:5002", flush=True)
    # threaded=False: one request at a time, so two requests never use the GPU together.
    app.run(port=5002, threaded=False)
