"""Parse CSV/XLSX test case files. Groups N rows per chunk, preserves headers."""
from pathlib import Path
from typing import Iterator

import pandas as pd


def parse(file_path: Path, rows_per_chunk: int = 5) -> Iterator[dict]:
    ext = file_path.suffix.lower()
    if ext in (".xlsx", ".xls"):
        df = pd.read_excel(file_path, dtype=str)
    else:
        df = pd.read_csv(file_path, dtype=str)

    df = df.fillna("").astype(str)
    headers = list(df.columns)
    header_line = " | ".join(headers)

    for chunk_idx, start in enumerate(range(0, len(df), rows_per_chunk)):
        rows = df.iloc[start : start + rows_per_chunk]
        lines = [header_line]
        for _, row in rows.iterrows():
            lines.append(" | ".join(row.tolist()))
        text = "\n".join(lines)

        yield {
            "text": text,
            "metadata": {
                "source_file": str(file_path),
                "source_type": "test_cases",
                "chunk_index": chunk_idx,
                "row_start": start,
                "row_end": start + len(rows) - 1,
            },
        }
