"""Fallback parser for plain text: transcripts, Lucid chart exports, general text."""
from pathlib import Path
from typing import Iterator

LINES_PER_BLOCK = 60


def parse(file_path: Path) -> Iterator[dict]:
    text = file_path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()

    for chunk_idx, start in enumerate(range(0, len(lines), LINES_PER_BLOCK)):
        block = "\n".join(lines[start : start + LINES_PER_BLOCK]).strip()
        if not block:
            continue
        yield {
            "text": block,
            "metadata": {
                "source_file": str(file_path),
                "source_type": "text",
                "chunk_index": chunk_idx,
            },
        }
