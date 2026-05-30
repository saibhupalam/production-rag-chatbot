from sentence_transformers import SentenceTransformer

model = SentenceTransformer(
    "nomic-ai/nomic-embed-text-v1.5",
    trust_remote_code=True   
)

def generate_embeddings(chunks: list[str]):
    embeddings = model.encode(
        chunks,
        convert_to_numpy = True
    )
    
    return embeddings
