import pytest
import numpy as np
from unittest.mock import patch, MagicMock
from app.utils.chunker import chunk_text
from app.rag.semantic_chunker import semantic_chunk_text, split_into_sentences
from app.services.embedding_service import generate_embeddings


def test_chunk_text_basic():
    text = "Short text under 500 characters."
    chunks = chunk_text(text)
    assert len(chunks) == 1
    assert chunks[0] == text


def test_chunk_text_long():
    text = "Sentence number one. " * 50
    chunks = chunk_text(text)
    assert len(chunks) > 1
    for c in chunks:
        assert len(c) <= 600


def test_split_into_sentences():
    text = "First sentence. Second sentence! Third sentence? Fourth sentence."
    sentences = split_into_sentences(text)
    assert len(sentences) >= 3


def test_semantic_chunking_short_fallback():
    text = "Short text."
    chunks = semantic_chunk_text(text)
    assert chunks == ["Short text."]


def test_semantic_chunking_empty():
    assert semantic_chunk_text("") == []
    assert semantic_chunk_text("   ") == []


@patch("app.services.embedding_service.get_embedding_model")
def test_generate_embeddings_task_prefix_convention(mock_get_model):
    mock_model = MagicMock()
    mock_model.encode.return_value = np.zeros((2, 768), dtype=np.float32)
    mock_get_model.return_value = mock_model

    chunks = ["First chunk", "Second chunk"]
    # Test document prefix
    doc_embs = generate_embeddings(chunks, is_query=False)
    args, kwargs = mock_model.encode.call_args
    passed_texts = args[0]
    assert passed_texts[0].startswith("search_document: ")
    assert doc_embs.shape == (2, 768)

    # Test query prefix
    query_embs = generate_embeddings(["Test question?"], is_query=True)
    args, kwargs = mock_model.encode.call_args
    assert args[0][0].startswith("search_query: ")
