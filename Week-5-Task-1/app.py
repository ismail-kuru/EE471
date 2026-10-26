import json

from flask import Flask, Response, jsonify, render_template, request, stream_with_context
from werkzeug.exceptions import RequestEntityTooLarge

import speech

app = Flask(__name__)
# Reject uploads larger than 10 MB before they reach Azure.
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024


@app.errorhandler(ValueError)
def bad_request(error):
    return jsonify(error=str(error)), 400


@app.errorhandler(RequestEntityTooLarge)
def too_large(error):
    return jsonify(error="Audio file is too large (max 10 MB)."), 413


@app.errorhandler(speech.NoSpeechError)
def no_speech(error):
    return jsonify(error=str(error)), 422


@app.errorhandler(speech.SpeechConfigError)
def not_configured(error):
    return jsonify(error=str(error)), 503


@app.errorhandler(speech.SpeechServiceError)
def azure_failed(error):
    return jsonify(error=str(error)), 502


def uploaded_audio():
    """Return the bytes of the uploaded "audio" file, or raise ValueError."""
    audio = request.files.get("audio")
    if audio is None:
        raise ValueError("Please record or choose an audio file.")
    return audio.read()


@app.get("/")
def index():
    return render_template(
        "index.html",
        voices=speech.VOICES,
        default_voice=speech.DEFAULT_VOICE,
        languages=speech.LANGUAGES,
        default_language=speech.DEFAULT_LANGUAGE,
        targets={code: name for code, (name, _) in speech.TRANSLATION_TARGETS.items()},
    )


@app.post("/api/tts")
def text_to_speech():
    """Body: {"text": "...", "voice": "en-US-JennyNeural"} → WAV audio."""
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ValueError("Request body must be a JSON object.")
    audio = speech.synthesize(data.get("text"), data.get("voice", speech.DEFAULT_VOICE))
    return Response(audio, mimetype="audio/wav")


@app.post("/api/stt")
def speech_to_text():
    """Form fields: audio (a WAV file) and language → {"text": "..."}."""
    language = request.form.get("language", speech.DEFAULT_LANGUAGE)
    return jsonify(text=speech.transcribe(uploaded_audio(), language))


@app.post("/api/diarize")
def diarize():
    """Form fields: audio and language → one JSON object per line, sent as Azure finds them."""
    language = request.form.get("language", speech.DEFAULT_LANGUAGE)
    phrases = speech.diarize(uploaded_audio(), language)
    lines = (json.dumps(phrase) + "\n" for phrase in phrases)
    return Response(stream_with_context(lines), mimetype="application/x-ndjson")


@app.post("/api/translate")
def translate():
    """Form fields: audio, source (e.g. tr-TR) and target (e.g. en) → original and translated text."""
    return jsonify(
        speech.translate(
            uploaded_audio(),
            request.form.get("source", speech.DEFAULT_LANGUAGE),
            request.form.get("target", "tr"),
        )
    )


@app.post("/api/pronunciation")
def pronunciation():
    """Form fields: audio and reference (the sentence that was read) → scores per sentence and word."""
    return jsonify(speech.assess_pronunciation(uploaded_audio(), request.form.get("reference")))


if __name__ == "__main__":
    # Port 5000 is taken by AirPlay Receiver on macOS.
    app.run(debug=True, port=5001)
