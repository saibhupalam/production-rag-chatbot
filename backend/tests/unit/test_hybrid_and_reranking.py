import pytest
from unittest.mock import patch, MagicMock
from app.rag.hybrid_search import tokenize, reciprocal_rank_fusion
from app.rag.reranker import rerank_candidates
from app.rag.query_rewriter import rewrite_query


def test_tokenize_preserves_technical_tokens():
    tokens = tokenize("Attention(Q, K, V) = softmax((Q @ K.T) / sqrt(d_k))")
    assert "attention" in tokens
    assert "sqrt" in tokens
    assert "d_k" in tokens


def test_reciprocal_rank_fusion():
    dense_results = [
        {"id": "doc_1", "text": "Dense item 1"},
        {"id": "doc_2", "text": "Dense item 2"},
    ]
    lexical_results = [
        {"id": "doc_2", "text": "Dense item 2"},
        {"id": "doc_3", "text": "Lexical item 3"},
    ]

    # doc_2 is present in both rankings so it should receive boosted RRF score
    fused = reciprocal_rank_fusion(dense_results, lexical_results, k=60)
    assert len(fused) == 3
    assert fused[0]["id"] == "doc_2"
    assert fused[0]["rrf_score"] > fused[1]["rrf_score"]


def test_rerank_candidates_disabled(monkeypatch):
    from app.core.config import settings
    monkeypatch.setattr(settings, "RERANKING_ENABLED", False)

    candidates = [
        {"text": "Chunk A"},
        {"text": "Chunk B"}
    ]
    result = rerank_candidates("query", candidates, top_k=1)
    assert len(result) == 1
    assert result[0]["text"] == "Chunk A"


@patch("app.rag.query_rewriter.llm")
def test_conversational_query_rewrite(mock_llm):
    mock_response = MagicMock()
    mock_response.content = "What is the scaling factor in self-attention formula?"
    mock_llm.invoke.return_value = mock_response

    history = [
        {"role": "user", "content": "Tell me about self-attention"},
        {"role": "assistant", "content": "Self attention uses Q, K, and V."}
    ]

    rewritten = rewrite_query("Explain its scaling factor.", history)
    assert "scaling factor" in rewritten.lower()


def test_conversational_query_rewrite_empty_history():
    query = "What is Transformer?"
    assert rewrite_query(query, []) == query
