from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct
from qdrant_client.models import (
    VectorParams,
    Distance
)

client = QdrantClient(
    host="localhost",
    port=6333
)

COLLECTION_NAME = "documents"


def create_collection():

    collections = client.get_collections()

    existing = [
        collection.name
        for collection
        in collections.collections
    ]

    if COLLECTION_NAME not in existing:

        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(
                size=768,
                distance=Distance.COSINE
            )
        )

        print("Collection created")

    else:

        print("Collection already exists")

def store_chunks(
    document_id: int,
    chunks: list[str],
    embeddings
):

    points = []

    for idx, (chunk, vector) in enumerate(
        zip(chunks, embeddings)
    ):

        points.append(
            PointStruct(
                id=document_id * 100000 + idx,

                vector=vector.tolist(),

                payload={
                    "document_id": document_id,
                    "chunk_id": idx,
                    "text": chunk
                }
            )
        )

    client.upsert(
        collection_name=COLLECTION_NAME,
        points=points
    )

    print(
        f"Stored {len(points)} chunks"
    )
    
def search_chunks(
    query_embedding,
    limit: int = 3
):

    results = client.query_points(
        collection_name=COLLECTION_NAME,

        query=query_embedding.tolist(),

        limit=limit
    )

    return results

