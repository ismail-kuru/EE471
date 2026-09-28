# EE471 – Modern Software Development Practices and Technologies

Coursework for EE 471 at Izmir Institute of Technology (Fall 2026).

## Repository layout

Each week and each project lives in its own folder with its own `README.md`
and, where needed, its own `requirements.txt`.

| Folder | Topic | Status |
|---|---|---|
| [`week01-conform/`](week01-conform/) | Brain teaser: *You Will All Conform* | Done |
| [`week05-azure-speech/`](week05-azure-speech/) | Azure AI Speech: text-to-speech and speech-to-text (Flask) | From previous term |

Upcoming folders: `week02-...` through `week12-...`, `projects/project1` through
`projects/project4`, and `final-project/`.

## Workflow

- `main` always holds finished, working code.
- Each week's work is done on its own branch (`Week1`, `Week2`, ...) and merged
  into `main` when complete.
- Project submissions are tagged (e.g. `project1-submission`).
- Secrets such as Azure keys go in a local `.env` file, which is never committed.
  Each project that needs one ships a `.env.example`.

## Archive

Work from the previous term is preserved in the `archive-2025-26` tag.
