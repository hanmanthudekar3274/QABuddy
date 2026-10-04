"""Parse Python/Java/TypeScript/JavaScript source files into text chunks."""
import ast
import re
from pathlib import Path
from typing import Iterator

SUPPORTED_EXTENSIONS = {".py", ".java", ".ts", ".js", ".tsx", ".jsx"}


def parse(file_path: Path) -> Iterator[dict]:
    """Yield raw text blocks with metadata. Each block = one function/class or fallback whole file."""
    text = file_path.read_text(encoding="utf-8", errors="replace")
    ext = file_path.suffix.lower()

    blocks = []
    if ext == ".py":
        blocks = _split_python(text)
    else:
        blocks = _split_generic(text)

    if not blocks:
        blocks = [text]

    for i, block in enumerate(blocks):
        block = block.strip()
        if not block:
            continue
        yield {
            "text": block,
            "metadata": {
                "source_file": str(file_path),
                "source_type": "code",
                "language": ext.lstrip("."),
                "block_index": i,
            },
        }


def _split_python(source: str) -> list[str]:
    """Split at top-level function and class boundaries via AST."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return _split_generic(source)

    lines = source.splitlines(keepends=True)
    boundaries = sorted(
        node.lineno - 1
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        and node.col_offset == 0
    )

    if not boundaries:
        return [source]

    blocks = []
    prev = 0
    for boundary in boundaries:
        chunk = "".join(lines[prev:boundary])
        if chunk.strip():
            blocks.append(chunk)
        prev = boundary
    blocks.append("".join(lines[prev:]))
    return blocks


def _split_generic(source: str) -> list[str]:
    """Split Java/TS/JS at method boundaries via regex."""
    pattern = re.compile(
        r"(?:(?:public|private|protected|static|async|function)\s+)"
        r"[\w<>\[\]]+\s+\w+\s*\(",
        re.MULTILINE,
    )
    boundaries = [m.start() for m in pattern.finditer(source)]
    if not boundaries:
        return [source]

    blocks = []
    prev = 0
    for b in boundaries:
        chunk = source[prev:b]
        if chunk.strip():
            blocks.append(chunk)
        prev = b
    blocks.append(source[prev:])
    return blocks
