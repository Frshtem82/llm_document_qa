"""مدیریت embedding و Qdrant vector store برای بازیابی معنایی."""
from typing import Optional
from django.conf import settings
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import QdrantVectorStore
from langchain_core.documents import Document as LangchainDocument
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, Filter, FieldCondition, MatchValue


COLLECTION_NAME = settings.QDRANT_COLLECTION

# LaBSE: 768 بعد
VECTOR_SIZE = 768

_embeddings_model: Optional[HuggingFaceEmbeddings] = None
_qdrant_client: Optional[QdrantClient] = None


def get_embeddings_model() -> HuggingFaceEmbeddings:
    global _embeddings_model
    if _embeddings_model is None:
        _embeddings_model = HuggingFaceEmbeddings(
            model_name="sentence-transformers/LaBSE",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True},
        )
    return _embeddings_model


def get_qdrant_client() -> QdrantClient:
    global _qdrant_client
    if _qdrant_client is None:
        _qdrant_client = QdrantClient(
            host=settings.QDRANT_HOST,
            port=settings.QDRANT_PORT,
        )
    return _qdrant_client


def ensure_collection_exists():
    client = get_qdrant_client()
    collections = client.get_collections().collections
    names = [c.name for c in collections]
    
    if COLLECTION_NAME not in names:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(
                size=VECTOR_SIZE,
                distance=Distance.COSINE,
            ),
        )


def reset_collection():
    client = get_qdrant_client()
    collections = client.get_collections().collections
    names = [c.name for c in collections]
    
    if COLLECTION_NAME in names:
        client.delete_collection(COLLECTION_NAME)
        print(f"🗑️ Collection '{COLLECTION_NAME}' deleted.")
    
    ensure_collection_exists()
    print(f"✅ Collection '{COLLECTION_NAME}' created with size={VECTOR_SIZE}.")


def get_vector_store() -> QdrantVectorStore:
    ensure_collection_exists()
    return QdrantVectorStore(
        client=get_qdrant_client(),
        collection_name=COLLECTION_NAME,
        embedding=get_embeddings_model(),
    )


def add_chunks_to_index(chunks) -> int:
    chunks = list(chunks)
    if not chunks:
        return 0
    
    vector_store = get_vector_store()
    
    langchain_docs = []
    ids = []
    for chunk in chunks:
        langchain_docs.append(
            LangchainDocument(
                page_content=chunk.content,
                metadata={
                    "chunk_id": chunk.id,
                    "document_id": chunk.document_id,
                    "document_title": chunk.document.title,
                    "chunk_index": chunk.chunk_index,
                }
            )
        )
        ids.append(chunk.id)
    
    vector_store.add_documents(documents=langchain_docs, ids=ids)
    return len(chunks)


def delete_document_from_index(document_id: int) -> int:
    client = get_qdrant_client()
    ensure_collection_exists()
    
    client.delete(
        collection_name=COLLECTION_NAME,
        points_selector=Filter(
            must=[
                FieldCondition(
                    key="metadata.document_id",
                    match=MatchValue(value=document_id),
                )
            ]
        ),
    )
    return 0


def search_similar_chunks(query: str, k: int = 4, document_id: Optional[int] = None) -> list:
    vector_store = get_vector_store()
    
    filter_condition = None
    if document_id is not None:
        filter_condition = Filter(
            must=[
                FieldCondition(
                    key="metadata.document_id",
                    match=MatchValue(value=document_id),
                )
            ]
        )
    
    results = vector_store.similarity_search_with_score(
        query=query,
        k=k,
        filter=filter_condition,
    )
    
    output = []
    for doc, score in results:
        output.append({
            "content": doc.page_content,
            "chunk_id": doc.metadata.get("chunk_id"),
            "document_id": doc.metadata.get("document_id"),
            "document_title": doc.metadata.get("document_title"),
            "chunk_index": doc.metadata.get("chunk_index"),
            "score": float(score),
        })
    return output


def rebuild_index() -> int:
    from .models import DocumentChunk
    
    reset_collection()
    chunks = DocumentChunk.objects.select_related('document').all()
    return add_chunks_to_index(chunks)


def get_index_count() -> int:
    try:
        client = get_qdrant_client()
        ensure_collection_exists()
        info = client.get_collection(COLLECTION_NAME)
        return info.points_count or 0
    except Exception:
        return 0