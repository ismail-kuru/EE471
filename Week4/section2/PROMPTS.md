# PROMPTS – Section 2

AI coding tool: **Claude Code** (Claude Opus 5.5).

## Main prompts

### Part 2 – CRUD methods

> Start from my Week 3 `custom_classes.py` and `main.py`. Add `ItemNotFoundError` and
> `ItemStateError`, unique integer ids that are never reused, `to_dict()` on every item,
> make `checkout()` / `return_item()` raise `ItemStateError` instead of returning
> "Already out", return the DVD reminder in the message instead of printing it, and add
> `get_item`, `list_items(available, item_type)`, `update_item(**fields)` and
> `remove_item` to `LibraryCollection`. In `main.py`, call every method once and
> trigger each exception with try/except.

### Part 3 – Flask REST API

> Expose `LibraryCollection` as a REST API in `app.py` with these 8 endpoints and status
> codes [table from the exercise]. Every response must be JSON, errors as
> `{"error": "<message>"}`. Routes should only translate HTTP to method calls; keep all
> rules in `custom_classes.py`. Seed at least 3 mixed items and add `requirements.txt`.

### Part 4 – Frontend

> I'm not doing the Figma design for the library, so use the example screenshot in the
> exercise: cards with title, author, type badge, pages/duration and an availability
> badge; Checkout/Return, edit and delete buttons; an "Available only" toggle and an
> All / Books / DVDs filter; an Add/Edit dialog whose last field switches between page
> count and duration; an empty state and an error area. Use `index.html`, `style.css`
> and `script.js`, served by Flask, and connect everything to the API. Show the API's
> error messages in the error area.

## Things the AI got wrong that I fixed

| # | Problem I found when reviewing / testing | Fix |
|---|---|---|
| 1 | **The success message was thrown away.** `script.js` called `/checkout` but ignored the response, so the DVD reminder ("Handle with care: Do not scratch the disc.") that Part 2 moved into the message never reached the user. | Success messages from the API are now shown in the message area in green; errors stay red. |
| 2 | **Non-JSON responses broke the error display.** `api()` always called `response.json()`. If the server sent an HTML error page (e.g. an unexpected 500), parsing failed and the user saw a confusing "Unexpected token <" instead of a message. | The parse is wrapped: such responses now show "Unexpected response from the server (500)." 204 (successful delete) is still read without a body. |

## Decisions I checked

- **No logic duplicated in JavaScript.** The "Available only" toggle and the type filter
  are sent to the API as `?available=true&type=book`; the page does not filter the list
  itself. Input checks (empty title, page count must be a positive integer) are also
  left to the API, so its 400 message appears in the form.
- **The delete button stays enabled for checked-out items** so the API can answer with
  409 and the page shows "Cannot delete 'Inception' while it is checked out."
- **Field name `duration`.** In Week 3 the field was renamed to `duration_minutes`
  during code review, but the exercise and the API example use `duration`, so it is
  `duration` again here; the unit (minutes) is in the docstring and the form label.
- **PUT vs PATCH.** PUT goes through `replace_item()`, which requires every editable
  field; PATCH goes through `update_item()`, which accepts any subset. The type of an
  item cannot be changed, so the type selector is locked while editing.
