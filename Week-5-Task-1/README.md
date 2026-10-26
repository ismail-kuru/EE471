# Week 5 – Task 1: Azure Speech Studio

A Flask website that uses Azure AI Speech.

- **Text to speech:** type text, pick a voice, and get a WAV file you can play or download.

## Setup

```bash
cd Week-5-Task-1
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env        # then put your Azure Speech key and region in .env
.venv/bin/python app.py     # http://127.0.0.1:5001
```

`.env` holds the secret key. It is listed in the repository's `.gitignore`, so it stays
on your computer and is never pushed. The scripts read it with `python-dotenv`.

## API

| Endpoint | Body | Success | Errors |
|---|---|---|---|
| `POST /api/tts` | `{"text": "Hello", "voice": "en-US-JennyNeural"}` | 200, `audio/wav` | 400 bad input, 502 Azure error, 503 missing key |
