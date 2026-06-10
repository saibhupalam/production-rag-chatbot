from app.services.embedding_service import (
    generate_embeddings
)

from app.services.qdrant_service import (
    store_chunks
)

chunks = [
    "Transformers use self attention",
    "RAG combines retrieval and generation"
]

embeddings = generate_embeddings(
    chunks
)

store_chunks(
    document_id=1,
    chunks=chunks,
    embeddings=embeddings
)