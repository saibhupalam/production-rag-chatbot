from app.services.embedding_service import (
    generate_embeddings
)

from app.services.qdrant_service import (
    search_chunks
)

from app.services.llm_service import (
    llm
)

from app.services.conversation_service import (
    get_conversation
)

from app.services.message_service import (
    get_conversation_messages,
    create_message
)

def answer_question(
    db,
    question: str,
    conversation_id: int
):

    conversation = get_conversation(
        db,
        conversation_id
    )

    if conversation is None:
        raise ValueError(
            f"Conversation {conversation_id} not found"
            )
    
    document_id = conversation.document_id

    messages = get_conversation_messages(
        db,
        conversation_id
    )

    history = "\n".join(
        [
            f"{msg.role}: {msg.content}"
            for msg in messages
        ]
    )

    create_message(
        db=db,
        conversation_id=conversation_id,
        role="user",
        content=question
    )

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

Conversation History:
{history}

Context:
{context}

Current Question:
{question}

Use ONLY the provided context.

If the answer is not present in the context,
say that the information is not available.
"""

    response = llm.invoke(
        prompt
    )

    create_message(
        db=db,
        conversation_id=conversation_id,
        role="assistant",
        content=response.content
    )

    return response.content