import sys
from pathlib import Path

from speech_service import synthesize_text_to_file


def main() -> int:
    text = " ".join(sys.argv[1:]).strip() or "Merhaba, Azure Speech Services hazir."
    output_path = Path("output.wav")

    try:
        synthesize_text_to_file(text=text, output_path=output_path)
        print(f"Audio written to {output_path.resolve()}")
        return 0
    except RuntimeError as exc:
        print(exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
