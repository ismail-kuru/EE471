# Week 5 – Task 1: Azure Speech Studio

A Flask website that uses Azure AI Speech, with two tabs:

- **Text to speech:** type text, pick a voice, and get a WAV file you can play or download.
- **Speech to text:** record from the microphone or upload an audio file, and get the
  transcript. The page converts every recording or upload to 16 kHz mono WAV in the
  browser, because that is the format the Azure Python SDK reads without extra tools.

The two features were built on separate branches (`text-to-speech` and `speech-to-text`)
and combined when merging into `main`.

## Setup

```bash
cd Week-5-Task-1
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env        # then put your Azure Speech key and region in .env
.venv/bin/python app.py     # http://127.0.0.1:5001
```

`.env` holds the secret key. It is listed in the repository's `.gitignore`, so it stays
on your computer and is never pushed. The scripts read it with `python-dotenv`. The same
key and region work for both features.

## API

| Endpoint | Body | Success | Errors |
|---|---|---|---|
| `POST /api/tts` | JSON: `{"text": "Hello", "voice": "en-US-JennyNeural"}` | 200, `audio/wav` | 400 bad input, 502 Azure error, 503 missing key |
| `POST /api/stt` | form data: `audio` (WAV file), `language` (`en-US` or `tr-TR`) | 200, `{"text": "..."}` | 400 bad input, 413 file too large, 422 no speech found, 502 Azure error, 503 missing key |
