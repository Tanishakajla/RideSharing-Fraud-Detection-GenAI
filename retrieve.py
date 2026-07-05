import json
from typing import Any

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

INDEX_PATH = "kb_index.faiss"
METADATA_PATH = "kb_metadata.json"

_model = SentenceTransformer("all-MiniLM-L6-v2")
_index = faiss.read_index(INDEX_PATH)

with open(METADATA_PATH, "r", encoding="utf-8") as f:
    _metadata = json.load(f)


def retrieve(query: str, top_k: int = 3) -> list[dict[str, Any]]:
    query_vec = np.asarray(
        _model.encode([query], normalize_embeddings=True),
        dtype=np.float32,
    )

    scores, indices = _index.search(query_vec, top_k)

    results: list[dict[str, Any]] = []

    for score, idx in zip(scores[0], indices[0]):
        if idx == -1:
            continue

        chunk = _metadata[idx]

        results.append(
            {
                "score": float(score),
                "source_file": chunk["source_file"],
                "section": chunk["section"],
                "text": chunk["text"],
            }
        )

    return results


if __name__ == "__main__":
    test_query = "many trips in a short time from a new account"

    for r in retrieve(test_query):
        print(f"[{r['score']}] {r['source_file']} / {r['section']}")
        print(r["text"][:150], "...\n")