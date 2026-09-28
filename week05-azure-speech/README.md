# Week 5 – Azure Speech Studio

Flask-based Azure Speech studio (text-to-speech and speech-to-text) for EE471 Week 5: Introduction to Cloud – Azure AI services.

## Features

- Accepts text input from a browser form on `localhost`
- Generates a `.wav` audio file with Azure Speech Services
- Uploads or records `.wav` audio and transcribes it back into text
- Plays generated audio in the page and lets you download it
- Keeps Azure credentials in a local `.env` file

## Setup

Run all commands from this folder:

```bash
cd week05-azure-speech
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Update `.env` with your own Azure Speech credentials:

```env
AZURE_SPEECH_KEY=your_azure_speech_key
AZURE_SPEECH_REGION=your_service_region
AZURE_SPEECH_VOICE=tr-TR-AhmetNeural
AZURE_SPEECH_RECOGNITION_LANGUAGE=tr-TR
```

## Run The Website

```bash
source .venv/bin/activate
flask --app app run --debug
```

Open `http://127.0.0.1:5000` in your browser.

## What You Can Do

- Text to speech: type text, choose voice, speed, and pitch, then generate a WAV file
- Speech to text: upload a WAV file or record from your microphone, then transcribe it with Azure

## Optional CLI Test

```bash
python speech_tts.py "Merhaba, Azure Speech Services hazir."
```
