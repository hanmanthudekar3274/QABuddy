"""Parse Jenkins log files. Strips ANSI codes; keeps log-level prefix in metadata."""
import re
from pathlib import Path
from typing import Iterator

ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")
LOG_LEVEL_RE = re.compile(r"\b(ERROR|WARN|INFO|DEBUG|FATAL)\b")
LINES_PER_CHUNK = 40  # raw lines per chunk before token re-chunking


def parse(file_path: Path) -> Iterator[dict]:
    raw = file_path.read_text(encoding="utf-8", errors="replace")
    clean = ANSI_RE.sub("", raw)
    lines = clean.splitlines()

    for chunk_idx, start in enumerate(range(0, len(lines), LINES_PER_CHUNK)):
        block_lines = lines[start : start + LINES_PER_CHUNK]
        text = "\n".join(block_lines)
        levels = set(LOG_LEVEL_RE.findall(text))
        yield {
            "text": text,
            "metadata": {
                "source_file": str(file_path),
                "source_type": "logs",
                "chunk_index": chunk_idx,
                "log_levels": list(levels),
            },
        }
