"""Token-window chunker using HuggingFace tokenizer (no Rust/tiktoken needed)."""
from typing import Iterator

from transformers import AutoTokenizer

_tokenizer = None


def _get_tokenizer():
    global _tokenizer
    if _tokenizer is None:
        # Use bge tokenizer — matches embedding model, max 512 tokens
        _tokenizer = AutoTokenizer.from_pretrained("BAAI/bge-large-en-v1.5")
    return _tokenizer


def token_count(text: str) -> int:
    tok = _get_tokenizer()
    return len(tok.encode(text, add_special_tokens=False))


def chunk_text(text: str, max_tokens: int, overlap_tokens: int) -> list[str]:
    tok = _get_tokenizer()
    ids = tok.encode(text, add_special_tokens=False)

    if len(ids) <= max_tokens:
        return [text]

    chunks = []
    start = 0
    while start < len(ids):
        end = min(start + max_tokens, len(ids))
        chunk_ids = ids[start:end]
        chunks.append(tok.decode(chunk_ids, skip_special_tokens=True))
        if end == len(ids):
            break
        start += max_tokens - overlap_tokens

    return chunks


def chunk_blocks(
    blocks: Iterator[dict],
    max_tokens: int,
    overlap_tokens: int,
) -> Iterator[dict]:
    for block in blocks:
        text = block["text"]
        meta = block["metadata"]
        sub_chunks = chunk_text(text, max_tokens, overlap_tokens)
        for sub_idx, sub_text in enumerate(sub_chunks):
            yield {
                "text": sub_text,
                "metadata": {**meta, "sub_chunk_index": sub_idx},
            }
