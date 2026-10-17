from typing import List, Dict, Any, Optional
import numpy as np
from app.core.config import settings
from app.services.embedding_service import generate_embeddings

_cross_encoder_model = None


def get_cross_encoder():
    """Lazy load CrossEncoder model if configured."""
    global _cross_encoder_model
    if _cross_encoder_model is None:
        try:
            from sentence_transformers import CrossEncoder
            _cross_encoder_model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
        except Exception as e:
            print(f"Notice: CrossEncoder not loaded ({e}), using embedding cross-scoring.")
            _cross_encoder_model = False
    return _cross_encoder_model


def rerank_candidates(
    query: str,
    candidates: List[Dict[str, Any]],
    top_k: int = 4
) -> List[Dict[str, Any]]:
    """
    Rerank candidate chunks against the user query.
    Uses CrossEncoder when available, with a fast embedding-similarity cross-scoring fallback
    reusing the existing Nomic embedder.
    Configurable via settings.RERANKING_ENABLED.
    """
    if not candidates:
        return []

    if not settings.RERANKING_ENABLED or len(candidates) <= 1:
        return candidates[:top_k]

    model = get_cross_encoder()

    if model:
        try:
            pairs = [[query, c["text"]] for c in candidates]
            scores = model.predict(pairs)
            for idx, c in enumerate(candidates):
                c["rerank_score"] = float(scores[idx])

            reranked = sorted(candidates, key=lambda x: x.get("rerank_score", 0.0), reverse=True)
            return reranked[:top_k]
        except Exception as e:
            print(f"Warning: CrossEncoder inference failed: {e}. Falling back to embedding reranker.")

    # High-accuracy fallback: compute cosine similarity against query with Nomic embedding model
    try:
        texts = [c["text"] for c in candidates]
        cand_embs = generate_embeddings(texts, is_query=False)
        query_emb = generate_embeddings([query], is_query=True)[0]

        # Normalize and compute cosine similarities
        cand_norms = np.linalg.norm(cand_embs, axis=1, keepdims=True)
        cand_norms[cand_norms == 0] = 1e-10
        norm_cands = cand_embs / cand_norms

        q_norm = np.linalg.norm(query_emb)
        if q_norm == 0:
            q_norm = 1e-10
        norm_q = query_emb / q_norm

        sims = np.dot(norm_cands, norm_q)

        for idx, c in enumerate(candidates):
            c["rerank_score"] = float(sims[idx])

        reranked = sorted(candidates, key=lambda x: x.get("rerank_score", 0.0), reverse=True)
        return reranked[:top_k]
    except Exception as e:
        print(f"Warning: Embedding reranking failed: {e}. Returning original candidates.")
        return candidates[:top_k]
