import re
import numpy as np
from typing import List, Optional
from app.utils.chunker import chunk_text as fallback_chunk_text
from app.services.embedding_service import generate_embeddings
from app.core.config import settings


def split_into_sentences(text: str) -> List[str]:
    """Split text into sentences using sentence boundary heuristics."""
    # Split on sentence ending punctuation followed by whitespace or newline
    sentence_endings = re.compile(r'(?<=[.!?])\s+(?=[A-Z0-9])|\n\n+')
    raw_sentences = sentence_endings.split(text.strip())
    sentences = [s.strip() for s in raw_sentences if s and len(s.strip()) > 5]
    return sentences if sentences else [text.strip()]


def semantic_chunk_text(
    text: str,
    min_chunk_size: int = 150,
    max_chunk_size: int = 800,
    similarity_threshold_percentile: float = 30.0
) -> List[str]:
    """
    Meaning-aware semantic chunking based on sentence embedding similarity.
    Reuses the existing Nomic embedding model to detect semantic topic boundaries.
    Falls back safely to RecursiveCharacterTextSplitter for short or malformed text.
    """
    if not text or not text.strip():
        return []

    cleaned = text.strip()
    if len(cleaned) <= max_chunk_size:
        return [cleaned]

    sentences = split_into_sentences(cleaned)
    if len(sentences) <= 2:
        return fallback_chunk_text(cleaned)

    try:
        # Generate sentence embeddings with Nomic document prefix
        sentence_embeddings = generate_embeddings(sentences, is_query=False)
        if len(sentence_embeddings) != len(sentences):
            return fallback_chunk_text(cleaned)

        # Calculate cosine similarities between consecutive sentences
        norms = np.linalg.norm(sentence_embeddings, axis=1, keepdims=True)
        norms[norms == 0] = 1e-10
        norm_embeddings = sentence_embeddings / norms

        similarities = [
            float(np.dot(norm_embeddings[i], norm_embeddings[i + 1]))
            for i in range(len(norm_embeddings) - 1)
        ]

        if not similarities:
            return fallback_chunk_text(cleaned)

        # Determine semantic breakpoint threshold
        breakpoint_threshold = float(np.percentile(similarities, similarity_threshold_percentile))

        chunks: List[str] = []
        current_sentences: List[str] = [sentences[0]]
        current_len = len(sentences[0])

        for i, sim in enumerate(similarities):
            next_sentence = sentences[i + 1]
            next_len = len(next_sentence)

            # Check if this is a semantic boundary or exceeds maximum allowed chunk length
            is_semantic_boundary = sim < breakpoint_threshold and current_len >= min_chunk_size
            exceeds_max = (current_len + next_len + 1) > max_chunk_size

            if is_semantic_boundary or exceeds_max:
                chunk_str = " ".join(current_sentences).strip()
                if chunk_str:
                    chunks.append(chunk_str)
                current_sentences = [next_sentence]
                current_len = next_len
            else:
                current_sentences.append(next_sentence)
                current_len += next_len + 1

        if current_sentences:
            final_chunk = " ".join(current_sentences).strip()
            if final_chunk:
                chunks.append(final_chunk)

        return chunks if chunks else fallback_chunk_text(cleaned)

    except Exception as e:
        # Safe fallback
        return fallback_chunk_text(cleaned)
