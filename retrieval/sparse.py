"""BM25 sparse vector encoder using rank-bm25 vocabulary approach."""
import math
import re
from collections import Counter


def tokenize(text: str) -> list[str]:
    return re.findall(r"\b\w+\b", text.lower())


class BM25SparseEncoder:
    """
    Lightweight BM25 encoder that produces Qdrant-compatible sparse vectors.
    Vocabulary is built incrementally during ingestion.
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.vocab: dict[str, int] = {}
        self.idf: dict[int, float] = {}
        self._doc_freqs: Counter = Counter()
        self._num_docs = 0
        self._avg_dl = 0.0
        self._total_tokens = 0

    def fit(self, texts: list[str]) -> None:
        self._num_docs = len(texts)
        total_tokens = 0
        for text in texts:
            tokens = set(tokenize(text))
            total_tokens += len(tokenize(text))
            for token in tokens:
                self._doc_freqs[token] += 1
                if token not in self.vocab:
                    self.vocab[token] = len(self.vocab)

        self._avg_dl = total_tokens / max(self._num_docs, 1)
        N = self._num_docs
        for token, idx in self.vocab.items():
            df = self._doc_freqs[token]
            self.idf[idx] = math.log((N - df + 0.5) / (df + 0.5) + 1)

    def encode(self, text: str) -> dict:
        tokens = tokenize(text)
        dl = len(tokens)
        tf = Counter(tokens)
        indices = []
        values = []
        for token, count in tf.items():
            if token not in self.vocab:
                continue
            idx = self.vocab[token]
            idf = self.idf.get(idx, 0.0)
            tf_norm = (count * (self.k1 + 1)) / (
                count + self.k1 * (1 - self.b + self.b * dl / max(self._avg_dl, 1))
            )
            score = float(idf * tf_norm)
            if score > 0:
                indices.append(idx)
                values.append(score)
        return {"indices": indices, "values": values}
