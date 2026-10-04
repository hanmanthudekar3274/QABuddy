"""Parse PDF files using pdfplumber. Strips headers/footers by y-coord threshold."""
from pathlib import Path
from typing import Iterator

import pdfplumber


HEADER_FOOTER_MARGIN = 50  # points from top/bottom edge to discard


def parse(file_path: Path) -> Iterator[dict]:
    full_text_pages = []
    with pdfplumber.open(file_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            h = page.height
            cropped = page.within_bbox(
                (0, HEADER_FOOTER_MARGIN, page.width, h - HEADER_FOOTER_MARGIN)
            )
            text = cropped.extract_text() or ""
            if text.strip():
                full_text_pages.append((page_num, text.strip()))

    # Yield per-page blocks; chunker will further split by token count
    for page_num, text in full_text_pages:
        yield {
            "text": text,
            "metadata": {
                "source_file": str(file_path),
                "source_type": "pdf",
                "page_number": page_num,
            },
        }
