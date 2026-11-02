# Mini Project 2: Voice-Activated Library App

The Week 4 Library App with voice control through Azure AI Speech. Click **Speak**, say a
command, and click **Send**. The app runs the matching API endpoint and reads the result
aloud, including errors.

## Setup

```bash
cd Mini-Project-2
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env        # then put your Azure Speech key and region in .env
.venv/bin/python app.py     # http://127.0.0.1:5001
```

`.env` holds the secret key and is never pushed (it is listed in the repository's
`.gitignore`). Library items are kept in memory, so restarting the server resets them.

## Voice commands

| Endpoint | You can say | The librarian answers |
|---|---|---|
| `POST /api/items` | "Create item, type book, title The Catcher in the Rye, author J.D. Salinger, pages 220" / "Add a DVD called Alien, directed by Ridley Scott, 117 minutes" | "Successfully created book 'The Catcher in the Rye' with ID 5." |
| `GET /api/items` | "List all items" / "Show available DVDs" / "Which books are checked out?" | "Found 2 available DVDs: 'Inception', 'Arrival'." |
| `GET /api/items/<id>` | "Get item 3" / "Tell me about item 3" | "Item 3 is the book '1984' by George Orwell, 328 pages. It is available." |
| `PUT /api/items/<id>` | "Replace item 3, title Emma, author Jane Austen, pages 400" | "Item 3 has been replaced. It is now the book 'Emma' by Jane Austen, 400 pages." |
| `PATCH /api/items/<id>` | "Update item 3, pages 200" / "Change the title of item 3 to Emma" | "Item 3 has been updated. It is now the book 'Emma' by George Orwell, 328 pages." |
| `DELETE /api/items/<id>` | "Delete item 3" / "Remove item 3" | "Item 3 has been deleted." |
| `POST /api/items/<id>/checkout` | "Check out item 3" / "Borrow item 3" | "Item 3, '1984', has been checked out." |
| `POST /api/items/<id>/return` | "Return item 3" / "Bring back item 3" | "Item 3, '1984', has been returned." |

Errors are spoken too:

| Status | You can say | The librarian answers |
|---|---|---|
| 400 | "Create item, type book, title Dune, author Frank Herbert" | "Sorry, missing fields for a book: page count." |
| 404 | "Get item 99" | "Sorry, item 99 was not found." |
| 409 | "Check out item 3" (twice) | "Sorry, item 3 is already checked out." |
| 409 | "Return item 3" (not checked out) | "Sorry, item 3 is not checked out." |
| 409 | "Delete item 3" (while checked out) | "Sorry, item 3 cannot be deleted while it is checked out." |

## How it works

1. `static/script.js` records the microphone, converts the recording to WAV and sends it to `POST /api/voice`.
2. `speech.listen()` turns the audio into text with Azure.
3. `commands.parse()` turns the text into a request, such as `POST /api/items/3/checkout`.
4. `run_command()` in `app.py` calls that endpoint, so voice and the page follow the same rules.
5. `replies.py` turns the status code and JSON into a sentence.
6. The page shows the sentence and plays it through `POST /api/speak`.

| File | Role |
|---|---|
| `custom_classes.py` | `Book`, `DVD` and `LibraryCollection` from Week 4: all library rules. |
| `app.py` | The Week 4 API routes, plus `/api/voice` and `/api/speak`. |
| `commands.py` | `parse()`: finds the action, item number and fields in recognized text. |
| `replies.py` | The sentences for each successful action and each error. |
| `speech.py` | Azure: `listen()` (speech to text) and `speak()` (text to speech). |
| `static/script.js` | The Week 4 page, plus recording and playing the replies. |

| Voice endpoint | Body | Success | Errors |
|---|---|---|---|
| `POST /api/voice` | form data: `audio` (WAV) | `{"heard", "action", "request", "status", "ok", "query", "reply"}` | 400, 413, 422 not understood, 502, 503 |
| `POST /api/speak` | `{"text": "Item 3 has been deleted."}` | `audio/wav` | 400, 502, 503 |

`POST /api/voice` returns 200 even if the library request was rejected, because the voice
command itself ran. The library's own status code is in `status`.
