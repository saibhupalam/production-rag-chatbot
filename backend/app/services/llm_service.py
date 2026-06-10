from langchain_groq import ChatGroq
from app.core.config import settings


llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=settings.GROQ_API_KEY
)