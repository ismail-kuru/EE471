from tempfile import NamedTemporaryFile
from pathlib import Path
from uuid import uuid4

from flask import Flask, jsonify, render_template, request, send_from_directory, url_for

from speech_service import (
    build_ssml_preview,
    get_default_recognition_language,
    get_default_voice,
    synthesize_text_to_file,
    transcribe_audio_file,
)


BASE_DIR = Path(__file__).resolve().parent
GENERATED_DIR = BASE_DIR / "generated"

DEMO_TEXTS = {
    "podcast": (
        "Welcome back to the show. Today we are exploring how high quality text "
        "to speech can transform content creation, accessibility, and productivity."
    ),
    "narration": (
        "In a quiet village surrounded by olive trees, a young inventor worked "
        "through the night, chasing an idea that could change everything."
    ),
    "product": (
        "Meet Voxify, your AI voice studio for natural, expressive, and "
        "multilingual speech generation."
    ),
}

VOICE_OPTIONS = [
    {"id": "tr-TR-AhmetNeural", "name": "Ahmet", "tag": "Warm", "language": "tr"},
    {"id": "tr-TR-EmelNeural", "name": "Emel", "tag": "Calm", "language": "tr"},
    {"id": "en-US-JennyNeural", "name": "Jenny", "tag": "Bright", "language": "en"},
    {"id": "en-US-GuyNeural", "name": "Guy", "tag": "Deep", "language": "en"},
]

LANGUAGE_OPTIONS = [
    {"id": "en", "name": "English"},
    {"id": "tr", "name": "Turkish"},
]

LANGUAGE_DEFAULT_VOICE = {
    "en": "en-US-JennyNeural",
    "tr": "tr-TR-AhmetNeural",
}

FEATURES = [
    "Speech To Text",
    "Studio Voices",
    "Custom Tone",
    "Export Audio",
]

RECOGNITION_LANGUAGE_OPTIONS = [
    {"id": "tr-TR", "name": "Turkish"},
    {"id": "en-US", "name": "English"},
]


def render_index(**overrides):
    text = overrides.get("text", DEMO_TEXTS["product"])
    selected_language = overrides.get("selected_language", "tr")
    selected_voice = overrides.get(
        "selected_voice",
        LANGUAGE_DEFAULT_VOICE.get(selected_language, get_default_voice()),
    )
    speed = float(overrides.get("speed", 1.0))
    pitch = float(overrides.get("pitch", 1.0))
    recognition_language = overrides.get(
        "recognition_language",
        get_default_recognition_language(),
    )

    context = {
        "demo_texts": DEMO_TEXTS,
        "voice_options": VOICE_OPTIONS,
        "language_options": LANGUAGE_OPTIONS,
        "recognition_language_options": RECOGNITION_LANGUAGE_OPTIONS,
        "feature_items": FEATURES,
        "text": text,
        "selected_language": selected_language,
        "selected_voice": selected_voice,
        "speed": speed,
        "pitch": pitch,
        "char_count": len(text),
        "word_count": len(text.split()) if text.strip() else 0,
        "estimated_seconds": int(((len(text.split()) / 150) * 60) + 0.9999) if text.strip() else 0,
        "ssml_preview": build_ssml_preview(text=text, voice_name=selected_voice, speed=speed, pitch=pitch),
        "default_voice": get_default_voice(),
        "recognition_language": recognition_language,
    }
    context.update(overrides)
    return render_template("index.html", **context)


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["GENERATED_DIR"] = GENERATED_DIR

    @app.get("/")
    def index():
        return render_index()

    @app.post("/synthesize")
    def synthesize():
        text = request.form.get("text", "").strip()
        selected_language = request.form.get("language", "tr").strip() or "tr"
        voice = request.form.get("voice", "").strip() or LANGUAGE_DEFAULT_VOICE.get(
            selected_language,
            get_default_voice(),
        )
        speed = float(request.form.get("speed", "1.0"))
        pitch = float(request.form.get("pitch", "1.0"))
        wants_json = request.headers.get("X-Requested-With") == "XMLHttpRequest"

        if not text:
            if wants_json:
                return jsonify({"error": "Please enter text to convert into speech."}), 400
            return render_index(
                error="Please enter text to convert into speech.",
                text=text,
                selected_language=selected_language,
                selected_voice=voice,
                speed=speed,
                pitch=pitch,
            ), 400

        filename = f"{uuid4().hex}.wav"
        output_path = app.config["GENERATED_DIR"] / filename

        try:
            synthesize_text_to_file(
                text=text,
                output_path=output_path,
                voice_name=voice,
                speed=speed,
                pitch=pitch,
            )
        except RuntimeError as exc:
            if wants_json:
                return jsonify({"error": str(exc)}), 500
            return render_index(
                error=str(exc),
                text=text,
                selected_language=selected_language,
                selected_voice=voice,
                speed=speed,
                pitch=pitch,
            ), 500

        audio_url = url_for("serve_audio", filename=filename)
        if wants_json:
            return jsonify(
                {
                    "message": "Audio file generated successfully.",
                    "audio_url": audio_url,
                    "filename": filename,
                }
            )
        return render_index(
            success="Audio file generated successfully.",
            text=text,
            selected_language=selected_language,
            selected_voice=voice,
            speed=speed,
            pitch=pitch,
            audio_url=audio_url,
            filename=filename,
        )

    @app.get("/audio/<path:filename>")
    def serve_audio(filename: str):
        return send_from_directory(app.config["GENERATED_DIR"], filename, as_attachment=False)

    @app.post("/transcribe")
    def transcribe():
        audio_file = request.files.get("audio_file")
        recognition_language = (
            request.form.get("recognition_language", get_default_recognition_language()).strip()
            or get_default_recognition_language()
        )

        if audio_file is None or not audio_file.filename:
            return jsonify({"error": "Please upload or record a WAV audio file first."}), 400

        suffix = Path(audio_file.filename).suffix.lower() or ".wav"
        if suffix != ".wav":
            return jsonify({"error": "Only WAV audio files are supported in this version."}), 400

        temp_path: Path | None = None

        try:
            with NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
                audio_file.save(temp_file)
                temp_path = Path(temp_file.name)

            transcript = transcribe_audio_file(
                audio_path=temp_path,
                recognition_language=recognition_language,
            )
            return jsonify({"transcript": transcript})
        except RuntimeError as exc:
            return jsonify({"error": str(exc)}), 500
        finally:
            if temp_path and temp_path.exists():
                temp_path.unlink()

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
