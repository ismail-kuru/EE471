# Mini Project 3: AI Art Chat

A web app that paints images from text prompts and chats with you by voice or by text.
All three models run locally on the computer; no API key or internet connection is needed
once they are downloaded.

**Figma design:** https://www.figma.com/design/RA9YPEQEK0TDM3iZZcVSz6/EE471-Mini-Project-3---AI-Art-Chat?node-id=2-25

## Features

1. **Prompt → image.** Write a prompt and press the paint button (or Enter). The image appears in
   the image box above.
2. **Voice → chatbot.** Press the mic button, speak, and press it again to stop. The words appear
   in the message box; edit them if needed and press send (or Enter). Your message and the
   chatbot's reply appear in the chat history.
3. **Chatbot → prompt.** Ask the chatbot for an image prompt, then click its answer to copy it
   into the prompt box (or copy and paste it), and press paint.

## Models

| Feature | Model | Size |
|---|---|---|
| Image generation | [stabilityai/sd-turbo](https://huggingface.co/stabilityai/sd-turbo): Stable Diffusion 2.1 distilled to make a 512×512 image in **one** step | 2.5 GB (float16) |
| Chatbot | [HuggingFaceTB/SmolLM2-360M-Instruct](https://huggingface.co/HuggingFaceTB/SmolLM2-360M-Instruct) | 0.7 GB |
| Speech to text | [openai/whisper-small](https://huggingface.co/openai/whisper-small) | 1 GB |

They run on the Mac GPU (MPS) when there is one, otherwise on the CPU. Tested on an Apple M2
with 16 GB of memory: an image takes about 3 s, a reply 2-6 s and a transcription about 2 s.

Whisper large-v3 was tried first, but on the Mac GPU it only works in float32 (about 6 GB);
next to the other two models that pushed the Mac into swap and made every request take over a
minute. Whisper small needs 1 GB and transcribes clear English just as well.

## Setup

Needs Python 3.9+ and ffmpeg (`brew install ffmpeg`), which decodes the browser's recordings.

```bash
cd Mini-Project-3
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python download_models.py     # about 3.4 GB, into ~/.cache/huggingface/hub
.venv/bin/python app.py                 # loads the models (about 10 s), then:
```

Open http://127.0.0.1:5002 in Chrome or Safari and allow the microphone.

## Files

| File | Role |
|---|---|
| `app.py` | Flask server: loads the models once at start, serves the page and three JSON endpoints. |
| `models.py` | One class per model: `ImageGenerator`, `Chatbot`, `SpeechToText`. |
| `templates/index.html` | The page, laid out like the Figma design. |
| `static/style.css` | The design's colors and sizes. |
| `static/app.js` | Paint, record and send: calls the endpoints and updates the page. |
| `download_models.py` | Downloads the models into the Hugging Face cache. |

## API

| Endpoint | Request | Response |
|---|---|---|
| `POST /api/image` | `{"prompt": "a lighthouse at dawn"}` | `{"image": "<base64 PNG>"}` |
| `POST /api/transcribe` | form field `audio`: the recording (webm or mp4) | `{"text": "..."}` |
| `POST /api/chat` | `{"messages": [{"role": "user", "content": "..."}]}` | `{"reply": "..."}` |
