# Week 5 – Task 2: Voice-Activated Calculator

The Week 4 calculator (which grew out of the Mini Project 1 `Calculator` class) with two
new abilities, both powered by Azure AI Speech:

- **Voice commands:** click the microphone button on the left, say a command such as
  “five plus two is”, and click it again. The calculator presses the keys for you.
- **Speaking keys:** every key says its word when pressed (“three”, “plus”, “five”), and
  `=` says the result (“is eight”).

Command table (in `commands.py`, used for both listening and speaking):

| Key | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | . | ÷ | × | + | − | = |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Word | zero | one | two | three | four | five | six | seven | eight | nine | point | over | times | plus | minus | is |

Azure often writes spoken numbers and operators as symbols (“5 + 2 is.”), so the parser
also accepts digits, `+ - * / =`, and a few homophones such as “to” for “two”.

## Setup

```bash
cd Week-5-Task-2
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env        # then put your Azure Speech key and region in .env
.venv/bin/python app.py     # http://127.0.0.1:5001
```

`.env` holds the secret key and is never pushed (see the repository's `.gitignore`).

## How it works

| File | Role |
|---|---|
| `custom_classes.py` | `Calculator` from Week 4: the four operations and input checks. |
| `commands.py` | The command table and `parse()`, which turns recognized text into keys. |
| `speech.py` | Azure: `speak()` (text to speech, cached) and `listen()` (speech to text, with the command words as a phrase list). |
| `app.py` | Flask routes: `/api/calculate`, `/api/speak`, `/api/voice`. |
| `static/script.js` | Keys, keyboard and voice commands all go through one `pressKey()`; speech is played in order through a queue. |

| Endpoint | Body | Success | Errors |
|---|---|---|---|
| `POST /api/calculate` | `{"a": 5, "b": 2, "operation": "add"}` | `{"result": 7}` | 400 |
| `POST /api/speak` | `{"text": "three"}` | `audio/wav` | 400, 502, 503 |
| `POST /api/voice` | form data: `audio` (WAV) | `{"heard": "5 + 2 is.", "keys": ["5", "+", "2", "="]}` | 400, 413, 422 no commands, 502, 503 |

