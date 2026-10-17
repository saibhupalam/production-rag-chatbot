from typing import List, Optional
import numpy as np
from sentence_transformers import SentenceTransformer

_model: Optional[SentenceTransformer] = None


def get_embedding_model() -> SentenceTransformer:
    """Lazy load the Nomic embedding model."""
    global _model
    if _model is None:
        _model = SentenceTransformer(
            "nomic-ai/nomic-embed-text-v1.5",
            trust_remote_code=True
        )
    return _model


def generate_embeddings(chunks: List[str], is_query: bool = False) -> np.ndarray:
    """
    Generate normalized embeddings for chunks or queries using nomic-ai/nomic-embed-text-v1.5.
    Applies the official task prefixes:
      - 'search_query: ' for queries
      - 'search_document: ' for document passages
    """
    if not chunks:
        return np.empty((0, 768), dtype=np.float32)

    model = get_embedding_model()
    prefix = "search_query: " if is_query else "search_document: "
    prefixed_chunks = [
        f"{prefix}{c}" if not c.startswith(prefix) else c
        for c in chunks
    ]

    embeddings = model.encode(
        prefixed_chunks,
        convert_to_numpy=True,
        normalize_embeddings=True
    )
    return embeddings
