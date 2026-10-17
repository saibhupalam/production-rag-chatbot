import uuid
from typing import Optional, List, Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.models import (
    PointStruct,
    VectorParams,
    Distance,
    Filter,
    FieldCondition,
    MatchValue
)
from app.core.config import settings

_client: Optional[QdrantClient] = None


def get_qdrant_client() -> QdrantClient:
    global _client
    if _client is None:
        _client = QdrantClient(
            host=settings.QDRANT_HOST,
            port=settings.QDRANT_PORT,
            check_compatibility=False,
            timeout=3.0
        )
    return _client


class _LazyClient:
    def __getattr__(self, name: str) -> Any:
        return getattr(get_qdrant_client(), name)


client = _LazyClient()

COLLECTION_NAME = settings.QDRANT_COLLECTION


def check_qdrant_health() -> bool:
    """Return True if Qdrant is accessible and responsive."""
    try:
        client.get_collections()
        return True
    except Exception:
        return False


def create_collection():
    """Ensure the target collection exists with cosine distance and 768 dimensions."""
    try:
        collections = client.get_collections()
        existing = [c.name for c in collections.collections]

        if COLLECTION_NAME not in existing:
            client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(
                    size=768,
                    distance=Distance.COSINE
                )
            )
            print(f"Collection '{COLLECTION_NAME}' created.")
        else:
            print(f"Collection '{COLLECTION_NAME}' already exists.")
    except Exception as e:
        print(f"Error checking/creating Qdrant collection: {e}")


def store_chunks(
    document_id: int,
    chunks: list[str],
    embeddings,
    user_id: Optional[int] = None
) -> int:
    """
    Store chunk vectors and payloads in Qdrant with deterministic UUIDs
    to prevent collision on repeat uploads and support user-level filtering.
    """
    create_collection()
    points = []

    for idx, (chunk, vector) in enumerate(zip(chunks, embeddings)):
        # Generate collision-free deterministic UUID based on document_id and chunk index
        point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"doc_{document_id}_idx_{idx}"))
        vec_list = vector.tolist() if hasattr(vector, "tolist") else list(vector)

        payload = {
            "document_id": int(document_id),
            "chunk_id": idx,
            "text": chunk
        }
        if user_id is not None:
            payload["user_id"] = int(user_id)

        points.append(
            PointStruct(
                id=point_id,
                vector=vec_list,
                payload=payload
            )
        )

    client.upsert(
        collection_name=COLLECTION_NAME,
        points=points
    )
    print(f"Stored {len(points)} chunks in Qdrant for document {document_id}")
    return len(points)


def search_chunks(
    query_embedding,
    document_id: int,
    user_id: Optional[int] = None,
    limit: int = 4
):
    """
    Dense vector search scoped to document_id (and optionally user_id).
    Compatible with Qdrant client 1.18.0 query_points API.
    """
    filter_conditions = [
        FieldCondition(
            key="document_id",
            match=MatchValue(value=int(document_id))
        )
    ]
    if user_id is not None:
        filter_conditions.append(
            FieldCondition(
                key="user_id",
                match=MatchValue(value=int(user_id))
            )
        )

    vec_list = query_embedding.tolist() if hasattr(query_embedding, "tolist") else list(query_embedding)

    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=vec_list,
        query_filter=Filter(must=filter_conditions),
        limit=limit
    )

    return results


def get_document_chunks(
    document_id: int,
    user_id: Optional[int] = None,
    limit: int = 500
) -> List[Dict[str, Any]]:
    """Retrieve all stored chunks for a specific document to enable lexical search."""
    filter_conditions = [
        FieldCondition(
            key="document_id",
            match=MatchValue(value=int(document_id))
        )
    ]
    if user_id is not None:
        filter_conditions.append(
            FieldCondition(
                key="user_id",
                match=MatchValue(value=int(user_id))
            )
        )

    try:
        points, _ = client.scroll(
            collection_name=COLLECTION_NAME,
            scroll_filter=Filter(must=filter_conditions),
            limit=limit,
            with_payload=True,
            with_vectors=False
        )
        return [
            {
                "id": p.id,
                "text": p.payload.get("text", ""),
                "chunk_id": p.payload.get("chunk_id", 0),
                "document_id": p.payload.get("document_id", document_id)
            }
            for p in points
        ]
    except Exception as e:
        print(f"Warning: Failed to scroll document chunks: {e}")
        return []


def delete_document_chunks(document_id: int):
    """Delete all chunks belonging to a document from Qdrant."""
    try:
        client.delete(
            collection_name=COLLECTION_NAME,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="document_id",
                        match=MatchValue(value=int(document_id))
                    )
                ]
            )
        )
    except Exception as e:
        print(f"Warning: Failed to delete chunks for document {document_id} from Qdrant: {e}")
