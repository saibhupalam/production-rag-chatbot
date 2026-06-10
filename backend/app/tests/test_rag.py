from app.services.rag_service import (
    answer_question
)

response = answer_question(
    question="What is self attention?",
    document_id=1
)

print(response)