
from __future__ import annotations
import logging
from typing import Optional
import chromadb
from chromadb.config import Settings as ChromaSettings

from .models import ExtractedChunk, ProcessedDocument, RetrievedEvidence
from .config import settings

logger = logging.getLogger(__name__)

# Global client (lazy init)
_client: Optional[chromadb.PersistentClient] = None
_collection = None
_COLLECTION_NAME = "legal_chunks"


def _get_collection():
    global _client, _collection
    if _collection is not None:
        return _collection

    _client = chromadb.PersistentClient(
        path=settings.chroma_db_path,
        settings=ChromaSettings(
            anonymized_telemetry=False,
            allow_reset=True
        ),
    )

    # Try to use sentence-transformers; fall back to default
    try:
        from chromadb.utils import embedding_functions
        ef = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=settings.embedding_model
        )
        logger.info(f"Using embedding model: {settings.embedding_model}")
    except Exception as e:
        logger.warning(f"sentence-transformers unavailable ({e}), using default embedding")
        ef = None

    kwargs = {"name": _COLLECTION_NAME, "metadata": {"hnsw:space": "cosine"}}
    if ef:
        kwargs["embedding_function"] = ef

    # Try to get existing collection first, then create if needed
    try:
        _collection = _client.get_collection(name=_COLLECTION_NAME, embedding_function=ef)
        logger.info(f"Using existing collection: {_COLLECTION_NAME}")
    except Exception:
        try:
            _collection = _client.create_collection(**kwargs)
            logger.info(f"Created new collection: {_COLLECTION_NAME}")
        except Exception as create_error:
            # If creation fails (e.g., already exists), try to get it again
            logger.warning(f"Collection creation failed, attempting to get existing: {create_error}")
            _collection = _client.get_collection(name=_COLLECTION_NAME, embedding_function=ef)
    
    return _collection


def index_document(doc: ProcessedDocument) -> int:
    """
    Add all chunks from a processed document into the vector store.
    Returns the number of chunks indexed.
    Idempotent — re-indexing the same document_id replaces existing entries.
    """
    if not doc.chunks:
        logger.warning(f"No chunks to index for {doc.filename}")
        return 0

    collection = _get_collection()

    # Delete existing entries for this document (supports re-processing)
    try:
        existing = collection.get(where={"document_id": doc.document_id})
        if existing["ids"]:
            collection.delete(ids=existing["ids"])
            logger.debug(f"Removed {len(existing['ids'])} stale chunks for {doc.document_id}")
    except Exception:
        pass

    ids = []
    documents = []
    metadatas = []

    for chunk in doc.chunks:
        if not chunk.text.strip():
            continue
        ids.append(chunk.chunk_id)
        documents.append(chunk.text)
        metadatas.append({
            "document_id": chunk.document_id,
            "filename": doc.filename,
            "page_number": chunk.page_number or -1,
            "chunk_index": chunk.chunk_index,
            "confidence": round(chunk.confidence, 3),
        })

    if not ids:
        return 0

    # ChromaDB batch upsert
    batch_size = 100
    for i in range(0, len(ids), batch_size):
        collection.upsert(
            ids=ids[i:i + batch_size],
            documents=documents[i:i + batch_size],
            metadatas=metadatas[i:i + batch_size],
        )

    logger.info(f"Indexed {len(ids)} chunks for {doc.filename}")
    return len(ids)


def retrieve_evidence(
    query: str,
    document_ids: Optional[list[str]] = None,
    n_results: int = None,
) -> list[RetrievedEvidence]:
    """
    Query the vector store and return ranked evidence chunks.

    Args:
        query: natural language query for the drafting task
        document_ids: restrict retrieval to these docs (None = all)
        n_results: how many chunks to return
    """
    collection = _get_collection()
    n_results = n_results or settings.max_retrieval_results

    where_filter = None
    if document_ids:
        if len(document_ids) == 1:
            where_filter = {"document_id": document_ids[0]}
        else:
            where_filter = {"document_id": {"$in": document_ids}}

    try:
        kwargs = {
            "query_texts": [query],
            "n_results": min(n_results, collection.count() or 1),
            "include": ["documents", "metadatas", "distances"],
        }
        if where_filter:
            kwargs["where"] = where_filter

        results = collection.query(**kwargs)
    except Exception as e:
        logger.error(f"Retrieval error: {e}")
        return []

    evidence = []
    for i, (doc_text, meta, distance) in enumerate(zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    )):
        # ChromaDB cosine distance: 0 = identical, 2 = opposite
        # Convert to similarity score 0-1
        similarity = max(0.0, 1.0 - distance / 2.0)

        evidence.append(RetrievedEvidence(
            chunk_id=results["ids"][0][i],
            document_id=meta["document_id"],
            text=doc_text,
            relevance_score=round(similarity, 4),
            page_number=meta.get("page_number") if meta.get("page_number", -1) >= 0 else None,
            source_filename=meta.get("filename", "unknown"),
        ))

    # Sort by relevance descending
    evidence.sort(key=lambda e: e.relevance_score, reverse=True)
    return evidence


def get_indexed_document_ids() -> list[str]:
    """Return all unique document IDs currently in the store."""
    collection = _get_collection()
    try:
        all_meta = collection.get(include=["metadatas"])
        ids = {m["document_id"] for m in all_meta["metadatas"]}
        return list(ids)
    except Exception:
        return []


def delete_document(document_id: str) -> int:
    """Remove all chunks for a given document. Returns count deleted."""
    collection = _get_collection()
    try:
        existing = collection.get(where={"document_id": document_id})
        if existing["ids"]:
            collection.delete(ids=existing["ids"])
            return len(existing["ids"])
    except Exception as e:
        logger.error(f"Error deleting document {document_id}: {e}")
    return 0
