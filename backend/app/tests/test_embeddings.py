from app.services.embedding_service import (
    generate_embeddings
)

chunks = [
    "Transformers use self attention",
    "RAG combines retrieval and generation"
]

embeddings = generate_embeddings(
    chunks
)

print(len(embeddings))

print(len(embeddings[0]))