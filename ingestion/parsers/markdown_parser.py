"""Parse Markdown files. Splits at H1/H2 boundaries to preserve section context."""
import re
from pathlib import Path
from typing import Iterator


HEADING_RE = re.compile(r"^#{1,2}\s+", re.MULTILINE)


def parse(file_path: Path) -> Iterator[dict]:
    text = file_path.read_text(encoding="utf-8", errors="replace")
    splits = HEADING_RE.split(text)
    headings = [""] + HEADING_RE.findall(text)

    for i, (heading, body) in enumerate(zip(headings, splits)):
        section = (heading + body).strip()
        if not section:
            continue
        yield {
            "text": section,
            "metadata": {
                "source_file": str(file_path),
                "source_type": "markdown",
                "section_index": i,
            },
        }
