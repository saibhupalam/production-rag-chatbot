from app.services.embedding_service import (
    generate_embeddings
)

from app.services.qdrant_service import (
    search_chunks
)

from app.services.llm_service import (
    llm
)


def answer_question(
    question: str,
    document_id: int
):

    query_embedding = generate_embeddings(
        [question]
    )[0]

    results = search_chunks(
        query_embedding=query_embedding,
        document_id=document_id
    )

    print("\nRetrieved Chunks:\n")

    for point in results.points:

        print("-" * 50)

        print(
            point.payload["text"]
        )

    context = "\n\n".join(
        [
            point.payload["text"]
            for point in results.points
        ]
    )

    prompt = f"""
You are a helpful assistant.

Use ONLY the provided context.

If the answer is not present in the context,
say that the information is not available.

Context:
{context}

Question:
{question}
"""

    response = llm.invoke(
        prompt
    )

    return response.content