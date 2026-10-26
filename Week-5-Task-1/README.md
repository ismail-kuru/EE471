# Week 5 – Task 1: Azure Speech Studio

A Flask website that uses Azure AI Speech, with five tabs:

- **Text to speech:** type text, pick a voice, and get a WAV file you can play or download.
- **Speech to text:** record from the microphone or upload an audio file, and get the
  transcript.
- **Diarization:** transcribe a conversation and label who is speaking. Lines appear on
  the page one by one while Azure is still working (real-time streaming).
- **Translation:** recognize speech in one language, translate it into another, and
  optionally hear the translation read aloud.
- **Pronunciation:** read a reference sentence aloud and get pronunciation, accuracy,
  fluency, completeness and prosody scores, with each word colored by its accuracy and
  skipped words marked.

Every audio feature converts recordings and uploads to 16 kHz mono WAV in the browser,
because that is the format the Azure Python SDK reads without extra tools.

Text to speech and speech to text were built on separate branches (`text-to-speech` and
`speech-to-text`) and combined when merging into `main`. The other three features were
added on `speech-extensions`.

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
| `POST /api/stt` | form data: `audio` (WAV), `language` (e.g. `en-US`) | 200, `{"text": "..."}` | 400, 413, 422, 502, 503 |
| `POST /api/diarize` | form data: `audio`, `language` | 200, one JSON object per line: `{"speaker": "Guest-1", "text": "..."}`, then `{"done": true}` | 400, 413, 502, 503; `{"error": "..."}` line if Azure fails midway |
| `POST /api/translate` | form data: `audio`, `source` (e.g. `tr-TR`), `target` (e.g. `en`) | 200, `{"recognized", "translation", "voice"}` | 400, 413, 422, 502, 503 |
| `POST /api/pronunciation` | form data: `audio`, `reference` (English sentence) | 200, `{"recognized", "scores", "words"}` | 400, 413, 422, 502, 503 |

Error codes: 400 bad input, 413 file larger than 10 MB, 422 no speech found, 502 Azure
error, 503 Azure key missing.
