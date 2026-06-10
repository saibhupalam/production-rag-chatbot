from app.services.qdrant_service import client

print(
    [method for method in dir(client)
     if "query" in method.lower()
     or "search" in method.lower()]
)
