import re
from typing import List, Dict, Any, Optional
from rank_bm25 import BM25Okapi
from app.services.embedding_service import generate_embeddings
from app.services.qdrant_service import search_chunks, get_document_chunks


def tokenize(text: str) -> List[str]:
    """Simple alphanumeric and punctuation-aware tokenization for lexical search."""
    # Keeps words, numbers, and technical tokens like snake_case or formulas
    tokens = re.findall(r'[a-zA-Z0-9_\-\.]+', text.lower())
    return tokens if tokens else text.lower().split()


def reciprocal_rank_fusion(
    dense_results: List[Dict[str, Any]],
    lexical_results: List[Dict[str, Any]],
    k: int = 60,
    dense_weight: float = 1.0,
    lexical_weight: float = 1.0
) -> List[Dict[str, Any]]:
    """
    Fuse dense and lexical rankings using Reciprocal Rank Fusion (RRF).
    RRF score = dense_weight / (k + rank_dense) + lexical_weight / (k + rank_lexical)
    """
    scores: Dict[str, float] = {}
    doc_map: Dict[str, Dict[str, Any]] = {}

    # Process dense rankings
    for rank, item in enumerate(dense_results):
        item_id = str(item.get("id", item.get("chunk_id", rank)))
        doc_map[item_id] = item
        scores[item_id] = scores.get(item_id, 0.0) + (dense_weight / (k + rank + 1))

    # Process lexical rankings
    for rank, item in enumerate(lexical_results):
        item_id = str(item.get("id", item.get("chunk_id", rank)))
        if item_id not in doc_map:
            doc_map[item_id] = item
        scores[item_id] = scores.get(item_id, 0.0) + (lexical_weight / (k + rank + 1))

    # Sort items by fused RRF score descending
    sorted_items = sorted(
        doc_map.keys(),
        key=lambda x: scores[x],
        reverse=True
    )

    fused_results = []
    for item_id in sorted_items:
        res = dict(doc_map[item_id])
        res["rrf_score"] = scores[item_id]
        fused_results.append(res)

    return fused_results


def hybrid_search(
    query: str,
    document_id: int,
    user_id: Optional[int] = None,
    limit: int = 6,
    candidate_depth: int = 12
) -> List[Dict[str, Any]]:
    """
    Hybrid retrieval combining dense semantic search and lexical BM25 search.
    - Dense search captures conceptual and semantic intent.
    - Lexical search captures exact terms, formulas, technical identifiers.
    - Fuses results with Reciprocal Rank Fusion (RRF).
    """
    # 1. Dense Semantic Retrieval
    dense_candidates: List[Dict[str, Any]] = []
    try:
        query_emb = generate_embeddings([query], is_query=True)[0]
        dense_qdrant = search_chunks(
            query_embedding=query_emb,
            document_id=document_id,
            user_id=user_id,
            limit=candidate_depth
        )
        for p in dense_qdrant.points:
            dense_candidates.append({
                "id": str(p.id),
                "text": p.payload.get("text", ""),
                "chunk_id": p.payload.get("chunk_id", 0),
                "document_id": p.payload.get("document_id", document_id),
                "dense_score": getattr(p, "score", 0.0),
                "retrieval_mode": "dense"
            })
    except Exception as e:
        print(f"Warning: Dense retrieval failed in hybrid search: {e}")

    # 2. Lexical Keyword Retrieval (BM25)
    lexical_candidates: List[Dict[str, Any]] = []
    try:
        all_chunks = get_document_chunks(document_id, user_id=user_id, limit=300)
        if all_chunks:
            tokenized_corpus = [tokenize(c["text"]) for c in all_chunks]
            bm25 = BM25Okapi(tokenized_corpus)
            tokenized_query = tokenize(query)

            if tokenized_query:
                doc_scores = bm25.get_scores(tokenized_query)
                # Sort indices by BM25 score
                top_indices = sorted(
                    range(len(doc_scores)),
                    key=lambda i: doc_scores[i],
                    reverse=True
                )[:candidate_depth]

                for idx in top_indices:
                    if doc_scores[idx] > 0:
                        c = all_chunks[idx]
                        lexical_candidates.append({
                            "id": str(c["id"]),
                            "text": c["text"],
                            "chunk_id": c["chunk_id"],
                            "document_id": c["document_id"],
                            "bm25_score": float(doc_scores[idx]),
                            "retrieval_mode": "lexical"
                        })
    except Exception as e:
        print(f"Warning: Lexical BM25 retrieval failed in hybrid search: {e}")

    # 3. Fallbacks if one mode has no results
    if not lexical_candidates:
        return dense_candidates[:limit]
    if not dense_candidates:
        return lexical_candidates[:limit]

    # 4. Fuse rankings using Reciprocal Rank Fusion
    fused = reciprocal_rank_fusion(
        dense_results=dense_candidates,
        lexical_results=lexical_candidates,
        k=60
    )
    return fused[:limit]
