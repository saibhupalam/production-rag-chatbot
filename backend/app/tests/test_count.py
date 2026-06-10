from app.services.qdrant_service import (
    client,
    COLLECTION_NAME
)

count = client.count(
    collection_name=COLLECTION_NAME
)

print(count)