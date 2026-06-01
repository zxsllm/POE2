from __future__ import annotations

import html
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TRANSCRIPT_DIR = ROOT / "data" / "youtube_transcripts"
LANG_PRIORITY = ("zh-Hans", "en", "en-orig", "zh-Hant")


def clean_vtt(path: Path) -> str:
    lines: list[str] = []
    previous = ""
    for raw in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw.strip()
        if not line:
            continue
        if line == "WEBVTT" or line.startswith("Kind:") or line.startswith("Language:"):
            continue
        if "-->" in line:
            continue
        if re.fullmatch(r"\d+", line):
            continue
        line = re.sub(r"<[^>]+>", "", line)
        line = html.unescape(line)
        line = re.sub(r"\s+", " ", line).strip()
        if not line or line == previous:
            continue
        lines.append(line)
        previous = line
    return "\n".join(lines).strip() + "\n"


def language_from_name(path: Path) -> str | None:
    stem = path.name.removesuffix(".vtt")
    for lang in LANG_PRIORITY:
        if stem.endswith(f".{lang}"):
            return lang
    return None


def main() -> int:
    if not TRANSCRIPT_DIR.exists():
        print(f"No transcript directory: {TRANSCRIPT_DIR}")
        return 1

    written = 0
    for path in sorted(TRANSCRIPT_DIR.glob("*.vtt")):
        lang = language_from_name(path)
        if not lang:
            continue
        text = clean_vtt(path)
        if not text.strip():
            continue
        out_path = path.with_suffix(".txt")
        out_path.write_text(text, encoding="utf-8")
        written += 1
        print(f"Wrote {out_path}")

    print(f"Cleaned transcripts: {written}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
