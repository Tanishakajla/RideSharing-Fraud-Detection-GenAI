import os
import re
import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

KB_DIR = "knowledge_base"
INDEX_PATH = "kb_index.faiss"
METADATA_PATH = "kb_metadata.json"

def chunk_markdown(filepath):
    """Split a markdown file into (section_title, section_text) chunks
    on '## ' headers. Keeps the '# Title' as context prepended to each chunk."""
    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()

    doc_title_match = re.match(r"# (.+)", text)
    doc_title = doc_title_match.group(1).strip() if doc_title_match else os.path.basename(filepath)

    sections = re.split(r"\n## ", text)
    chunks = []
    for section in sections[1:]:  # skip the part before the first "## "
        lines = section.split("\n", 1)
        section_title = lines[0].strip()
        section_body = lines[1].strip() if len(lines) > 1 else ""
        # Prepend doc + section title so the embedding captures full context,
        # not just an isolated paragraph.
        chunk_text = f"{doc_title} - {section_title}\n{section_body}"
        chunks.append({
            "text": chunk_text,
            "source_file": os.path.basename(filepath),
            "doc_title": doc_title,
            "section": section_title
        })
    return chunks

def build_index():
    all_chunks = []
    for fname in os.listdir(KB_DIR):
        if fname.endswith(".md"):
            all_chunks.extend(chunk_markdown(os.path.join(KB_DIR, fname)))

    print(f"Built {len(all_chunks)} chunks from {KB_DIR}/")

    model = SentenceTransformer("all-MiniLM-L6-v2")
    texts = [c["text"] for c in all_chunks]
    embeddings = model.encode(texts, normalize_embeddings=True)  # normalize -> cosine similarity via inner product
    embeddings = np.array(embeddings).astype("float32")

    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)  # IP = inner product = cosine similarity, since vectors are normalized
    index.add(embeddings)

    faiss.write_index(index, INDEX_PATH)
    with open(METADATA_PATH, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, indent=2)

    print(f"Saved index to {INDEX_PATH} and metadata to {METADATA_PATH}")

if __name__ == "__main__":
    build_index()