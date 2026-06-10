from app.services.rag_service import (
    answer_question
)

response = answer_question(
    "What is self attention?"
)

print(response)