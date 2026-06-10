from app.services.embedding_service import (
    generate_embeddings
)

from app.services.qdrant_service import (
    search_chunks
)

query = "What is self attention?"

embedding = generate_embeddings(
    [query]
)

results = search_chunks(
    embedding[0]
)

for result in results.points:

    print(result.score)

    print(
        result.payload["text"]
    )