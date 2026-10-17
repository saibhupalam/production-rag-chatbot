import time
from typing import List, Dict, Any, Tuple
import numpy as np
from rank_bm25 import BM25Okapi

from app.utils.chunker import chunk_text
from app.rag.semantic_chunker import semantic_chunk_text
from app.rag.hybrid_search import reciprocal_rank_fusion, tokenize
from app.services.embedding_service import generate_embeddings

# Curated Technical Benchmark Dataset for RAG Evaluation
EVALUATION_DOCUMENTS = [
    {
        "id": 1,
        "title": "Transformer Attention Mechanisms",
        "text": """
The Transformer architecture relies entirely on attention mechanisms to draw global dependencies between input and output.
The fundamental self-attention formula is defined as Attention(Q, K, V) = softmax((Q @ K.T) / sqrt(d_k)) @ V.
Here, Q represents queries, K represents keys, and V represents values, each with dimension d_k.
The scaling factor 1 / sqrt(d_k) counteracts the effect of large dot products pushing the softmax function into regions with small gradients.

Multi-Head Attention allows the model to jointly attend to information from different representation subspaces at different positions.
MultiHead(Q, K, V) = Concat(head_1, ..., head_h) @ W_O, where head_i = Attention(Q @ W_Q_i, K @ W_K_i, V @ W_V_i).
The projection parameter matrices are W_Q_i in R^(d_model x d_k), W_K_i in R^(d_model x d_k), and W_O in R^(h*d_v x d_model).

In addition to attention sub-layers, each layer contains a fully connected Feed-Forward Network (FFN).
The FFN equation is FFN(x) = max(0, x @ W_1 + b_1) @ W_2 + b_2, consisting of two linear transformations with a ReLU activation in between.
Residual connections surround each sub-layer, followed by layer normalization: LayerNorm(x + Sublayer(x)).

Positional encodings are added to input embeddings because the Transformer contains no recurrence or convolution.
Sinusoidal positional encodings use frequencies: PE(pos, 2i) = sin(pos / 10000^(2i/d_model)) and PE(pos, 2i+1) = cos(pos / 10000^(2i/d_model)).
These fixed wavelengths allow the model to learn to attend by relative positions easily.
"""
    }
]

EVALUATION_QUERIES = [
    {
        "id": "q1_semantic",
        "query": "How do attention mechanisms prevent vanishing gradients when dot products grow large?",
        "target_keywords": ["scaling factor", "sqrt(d_k)", "counteracts"],
        "type": "semantic_concept"
    },
    {
        "id": "q2_exact_formula",
        "query": "Attention(Q, K, V) = softmax((Q @ K.T) / sqrt(d_k)) @ V",
        "target_keywords": ["softmax((Q @ K.T) / sqrt(d_k))", "Attention(Q, K, V)"],
        "type": "exact_formula"
    },
    {
        "id": "q3_technical_identifier",
        "query": "What is the projection parameter matrix W_O dimension in multi-head attention?",
        "target_keywords": ["W_O in R^(h*d_v x d_model)", "MultiHead(Q, K, V)"],
        "type": "technical_identifier"
    },
    {
        "id": "q4_ffn_relu",
        "query": "What is the activation function and equation used in the Feed-Forward Network?",
        "target_keywords": ["FFN(x) = max(0, x @ W_1 + b_1)", "ReLU"],
        "type": "semantic_and_symbolic"
    },
    {
        "id": "q5_positional_sin",
        "query": "PE(pos, 2i) = sin(pos / 10000^(2i/d_model))",
        "target_keywords": ["PE(pos, 2i)", "Sinusoidal positional encodings"],
        "type": "exact_code_formula"
    }
]


def is_chunk_relevant(chunk_text: str, target_keywords: List[str]) -> bool:
    """Evaluate whether a retrieved chunk contains the expected ground-truth information."""
    chunk_lower = chunk_text.lower()
    return any(kw.lower() in chunk_lower for kw in target_keywords)


def calculate_metrics(
    retrieved_chunks: List[str],
    target_keywords: List[str],
    k: int = 3
) -> Dict[str, float]:
    """Calculate HitRate@K, Precision@K, Recall@K, and MRR."""
    top_k_chunks = retrieved_chunks[:k]
    hits = [is_chunk_relevant(c, target_keywords) for c in top_k_chunks]

    hit_rate = 1.0 if any(hits) else 0.0
    precision = sum(hits) / max(len(top_k_chunks), 1)

    # In our benchmark each query has 1 primary relevant passage in the document
    recall = 1.0 if any(hits) else 0.0

    # Mean Reciprocal Rank
    mrr = 0.0
    for rank, hit in enumerate(hits):
        if hit:
            mrr = 1.0 / (rank + 1)
            break

    return {
        f"HitRate@{k}": hit_rate,
        f"Precision@{k}": precision,
        f"Recall@{k}": recall,
        "MRR": mrr
    }


def run_dense_retrieval(query: str, chunks: List[str], k: int = 3) -> Tuple[List[str], float]:
    """Baseline retrieval: Recursive character chunks + Dense embeddings."""
    t0 = time.perf_counter()
    chunk_embs = generate_embeddings(chunks, is_query=False)
    query_emb = generate_embeddings([query], is_query=True)[0]

    # Cosine similarity
    chunk_norms = np.linalg.norm(chunk_embs, axis=1, keepdims=True)
    chunk_norms[chunk_norms == 0] = 1e-10
    norm_chunks = chunk_embs / chunk_norms

    q_norm = np.linalg.norm(query_emb)
    if q_norm == 0:
        q_norm = 1e-10
    norm_q = query_emb / q_norm

    sims = np.dot(norm_chunks, norm_q)
    ranked_indices = np.argsort(sims)[::-1][:k]
    latency_ms = (time.perf_counter() - t0) * 1000.0

    return [chunks[i] for i in ranked_indices], latency_ms


def run_hybrid_retrieval(query: str, chunks: List[str], k: int = 3) -> Tuple[List[str], float]:
    """Advanced retrieval: Semantic chunks + Hybrid (Dense + BM25) with RRF."""
    t0 = time.perf_counter()

    # Dense candidate ranking
    chunk_embs = generate_embeddings(chunks, is_query=False)
    query_emb = generate_embeddings([query], is_query=True)[0]

    chunk_norms = np.linalg.norm(chunk_embs, axis=1, keepdims=True)
    chunk_norms[chunk_norms == 0] = 1e-10
    norm_chunks = chunk_embs / chunk_norms
    q_norm = np.linalg.norm(query_emb)
    if q_norm == 0:
        q_norm = 1e-10
    norm_q = query_emb / q_norm

    sims = np.dot(norm_chunks, norm_q)
    dense_ranked = [
        {"id": str(i), "text": chunks[i], "dense_score": float(sims[i])}
        for i in np.argsort(sims)[::-1]
    ]

    # BM25 Lexical candidate ranking
    tokenized_corpus = [tokenize(c) for c in chunks]
    bm25 = BM25Okapi(tokenized_corpus)
    tokenized_q = tokenize(query)
    bm25_scores = bm25.get_scores(tokenized_q)
    lexical_ranked = [
        {"id": str(i), "text": chunks[i], "bm25_score": float(bm25_scores[i])}
        for i in np.argsort(bm25_scores)[::-1]
        if bm25_scores[i] > 0
    ]

    # Reciprocal Rank Fusion
    fused = reciprocal_rank_fusion(
        dense_results=dense_ranked,
        lexical_results=lexical_ranked,
        k=60
    )

    ranked_chunks = [item["text"] for item in fused[:k]]
    latency_ms = (time.perf_counter() - t0) * 1000.0
    return ranked_chunks, latency_ms


def evaluate_rag_pipeline(k: int = 3) -> Dict[str, Any]:
    """
    Execute full comparative benchmark between Baseline and Advanced RAG retrieval pipelines.
    Returns aggregated metrics, latency numbers, and per-query details.
    """
    doc_text = EVALUATION_DOCUMENTS[0]["text"]

    # Baseline chunking: Recursive Character Splitter
    baseline_chunks = chunk_text(doc_text)

    # Advanced chunking: Semantic Chunking
    advanced_chunks = semantic_chunk_text(doc_text)

    baseline_metrics_list = []
    baseline_latencies = []

    advanced_metrics_list = []
    advanced_latencies = []

    query_details = []

    for q in EVALUATION_QUERIES:
        query_text = q["query"]
        targets = q["target_keywords"]

        # Run Baseline
        base_retrieved, base_lat = run_dense_retrieval(query_text, baseline_chunks, k=k)
        base_metrics = calculate_metrics(base_retrieved, targets, k=k)
        baseline_metrics_list.append(base_metrics)
        baseline_latencies.append(base_lat)

        # Run Advanced
        adv_retrieved, adv_lat = run_hybrid_retrieval(query_text, advanced_chunks, k=k)
        adv_metrics = calculate_metrics(adv_retrieved, targets, k=k)
        advanced_metrics_list.append(adv_metrics)
        advanced_latencies.append(adv_lat)

        query_details.append({
            "query_id": q["id"],
            "type": q["type"],
            "baseline_mrr": base_metrics["MRR"],
            "advanced_mrr": adv_metrics["MRR"],
            "baseline_hit": base_metrics[f"HitRate@{k}"],
            "advanced_hit": adv_metrics[f"HitRate@{k}"]
        })

    def average_metric(metric_list: List[Dict[str, float]], key: str) -> float:
        return sum(m[key] for m in metric_list) / len(metric_list)

    summary = {
        "k": k,
        "queries_count": len(EVALUATION_QUERIES),
        "baseline": {
            f"HitRate@{k}": average_metric(baseline_metrics_list, f"HitRate@{k}"),
            f"Precision@{k}": average_metric(baseline_metrics_list, f"Precision@{k}"),
            f"Recall@{k}": average_metric(baseline_metrics_list, f"Recall@{k}"),
            "MRR": average_metric(baseline_metrics_list, "MRR"),
            "mean_latency_ms": sum(baseline_latencies) / len(baseline_latencies)
        },
        "advanced": {
            f"HitRate@{k}": average_metric(advanced_metrics_list, f"HitRate@{k}"),
            f"Precision@{k}": average_metric(advanced_metrics_list, f"Precision@{k}"),
            f"Recall@{k}": average_metric(advanced_metrics_list, f"Recall@{k}"),
            "MRR": average_metric(advanced_metrics_list, "MRR"),
            "mean_latency_ms": sum(advanced_latencies) / len(advanced_latencies)
        },
        "query_details": query_details
    }

    return summary


if __name__ == "__main__":
    results = evaluate_rag_pipeline(k=3)
    print("=== RAG Evaluation Results ===")
    print(f"Total Queries: {results['queries_count']} (k={results['k']})")
    print(f"Baseline MRR: {results['baseline']['MRR']:.4f} | Advanced MRR: {results['advanced']['MRR']:.4f}")
    print(f"Baseline HitRate@3: {results['baseline']['HitRate@3']:.4f} | Advanced HitRate@3: {results['advanced']['HitRate@3']:.4f}")
    print(f"Baseline Latency: {results['baseline']['mean_latency_ms']:.2f}ms | Advanced Latency: {results['advanced']['mean_latency_ms']:.2f}ms")
