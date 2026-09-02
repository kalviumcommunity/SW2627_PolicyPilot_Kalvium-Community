"""Vector database storage and retrieval service for PolicyPilot RAG Assistant.

Manages ChromaDB vector collections, enforces embedding vector dimensions,
stores dense vectors alongside source chunk text and rich metadata, and provides
fast nearest-neighbor semantic search and exact record readback.
"""

import os
import logging
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
import chromadb
from chromadb.api import ClientAPI
from chromadb.config import Settings

load_dotenv()
logger = logging.getLogger(__name__)


class VectorStoreService:
    """Service to manage vector database collections, record storage, and retrieval."""

    DEFAULT_COLLECTION_NAME = "rag_chunks"
    DEFAULT_DIMENSION = 1536
    DEFAULT_METRIC = "cosine"

    def __init__(
        self,
        persist_directory: Optional[str] = None,
        in_memory: bool = False,
        client: Optional[ClientAPI] = None,
        default_collection: str = DEFAULT_COLLECTION_NAME,
        dimension: int = DEFAULT_DIMENSION,
    ):
        """Initialize VectorStoreService with persistent directory or in-memory client.

        Args:
            persist_directory: Path to persist ChromaDB files. Falls back to CHROMA_PERSIST_DIR,
                               VECTOR_DB_PATH, or 'outputs/chroma_db'.
            in_memory: If True, uses ephemeral in-memory storage (ideal for tests).
            client: Optional pre-configured ChromaDB Client instance.
            default_collection: Default collection name to use if not specified.
            dimension: Expected vector dimensionality for the collection (default: 1536).
        """
        self.persist_directory = (
            persist_directory
            or os.getenv("CHROMA_PERSIST_DIR")
            or os.getenv("VECTOR_DB_PATH")
            or os.path.join("outputs", "chroma_db")
        )
        self.in_memory = in_memory
        self.default_collection = default_collection
        self.dimension = dimension
        self._client: Optional[ClientAPI] = client
        self._collections: Dict[str, Any] = {}

    def get_client(self) -> ClientAPI:
        """Get or initialize the ChromaDB client instance."""
        if self._client is None:
            if self.in_memory or self.persist_directory == ":memory:":
                logger.info("Initializing in-memory ChromaDB client")
                self._client = chromadb.EphemeralClient(
                    settings=Settings(anonymized_telemetry=False, is_persistent=False)
                )
            else:
                os.makedirs(self.persist_directory, exist_ok=True)
                logger.info("Initializing persistent ChromaDB client at: %s", self.persist_directory)
                self._client = chromadb.PersistentClient(
                    path=self.persist_directory,
                    settings=Settings(anonymized_telemetry=False, is_persistent=True),
                )
        return self._client

    def get_or_create_collection(
        self,
        name: Optional[str] = None,
        dimension: Optional[int] = None,
        metric: str = DEFAULT_METRIC,
    ) -> Any:
        """Create or retrieve a collection with specified dimension and distance metric.

        Args:
            name: Collection name. Defaults to self.default_collection.
            dimension: Expected vector dimension. Defaults to self.dimension.
            metric: Distance metric ('cosine', 'l2', or 'ip'). Default is 'cosine'.

        Returns:
            ChromaDB Collection instance.
        """
        col_name = name or self.default_collection
        expected_dim = dimension or self.dimension

        client = self.get_client()

        # Chroma metadata configuration for distance space and dimension tracking
        metadata = {
            "hnsw:space": metric,
            "dimension": expected_dim,
        }

        collection = client.get_or_create_collection(
            name=col_name,
            metadata=metadata,
        )
        self._collections[col_name] = {
            "collection": collection,
            "dimension": expected_dim,
            "metric": metric,
        }
        return collection

    def validate_vector_dimension(
        self, vector: List[float], expected_dim: Optional[int] = None
    ) -> None:
        """Verify that a vector's length matches the expected dimension.

        Raises:
            ValueError: If vector dimension does not match expected dimension.
        """
        target_dim = expected_dim or self.dimension
        if len(vector) != target_dim:
            raise ValueError(
                f"Vector dimension mismatch: expected {target_dim} values, got {len(vector)}"
            )

    def upsert_record(
        self,
        id: str,
        vector: List[float],
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
        collection_name: Optional[str] = None,
    ) -> str:
        """Insert or update a single record in the collection.

        Args:
            id: Unique identifier for the chunk.
            vector: Dense embedding vector.
            text: Original chunk text.
            metadata: Metadata dictionary (e.g. source document, chunk index, section).
            collection_name: Optional collection name.

        Returns:
            The upserted record ID.
        """
        self.upsert_records(
            records=[{
                "id": id,
                "vector": vector,
                "text": text,
                "metadata": metadata or {},
            }],
            collection_name=collection_name,
        )
        return id

    def upsert_records(
        self,
        records: List[Dict[str, Any]],
        collection_name: Optional[str] = None,
    ) -> List[str]:
        """Insert or update multiple records in the vector database collection.

        Each record dictionary must conform to the schema:
        {
            "id": "stable chunk id",
            "vector": [float, ...],
            "text": "original chunk text",
            "metadata": {"source": "...", "chunk_index": 0, ...}
        }

        Args:
            records: List of record dictionaries.
            collection_name: Optional collection name.

        Returns:
            List of upserted record IDs.
        """
        if not records:
            return []

        col_name = collection_name or self.default_collection
        collection = self.get_or_create_collection(name=col_name)
        target_dim = self._collections.get(col_name, {}).get("dimension", self.dimension)

        ids: List[str] = []
        embeddings: List[List[float]] = []
        documents: List[str] = []
        metadatas: List[Dict[str, Any]] = []

        # Deduplicate by ID within the batch (keeping latest occurrence)
        deduped_records: Dict[str, Dict[str, Any]] = {}
        for idx, rec in enumerate(records):
            rec_id = rec.get("id")
            if not rec_id:
                raise ValueError(f"Record at index {idx} is missing required 'id' field")
            deduped_records[str(rec_id)] = rec

        for rec_id, rec in deduped_records.items():
            # Support both 'vector' and 'embedding' keys
            vector = rec.get("vector") or rec.get("embedding")
            if vector is None:
                raise ValueError(f"Record '{rec_id}' is missing required vector/embedding")

            self.validate_vector_dimension(vector, expected_dim=target_dim)

            text = rec.get("text", "")
            meta = rec.get("metadata", {}) or {}

            # Sanitize metadata: chroma requires primitive types (str, int, float, bool)
            clean_meta = {}
            for k, v in meta.items():
                if isinstance(v, (str, int, float, bool)):
                    clean_meta[k] = v
                elif v is not None:
                    clean_meta[k] = str(v)

            ids.append(rec_id)
            embeddings.append(vector)
            documents.append(text)
            metadatas.append(clean_meta)

        collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )

        return ids

    def get_record(
        self,
        id: str,
        collection_name: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Read back a single stored record by its ID with full vector, text, and metadata.

        Args:
            id: The record ID to retrieve.
            collection_name: Optional collection name.

        Returns:
            Dictionary containing 'id', 'vector', 'vector_length', 'text', and 'metadata',
            or None if record does not exist.
        """
        results = self.get_records(ids=[id], collection_name=collection_name)
        return results[0] if results else None

    def get_records(
        self,
        ids: List[str],
        collection_name: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Read back multiple stored records by IDs.

        Args:
            ids: List of record IDs.
            collection_name: Optional collection name.

        Returns:
            List of dictionaries containing 'id', 'vector', 'vector_length', 'text', 'metadata'.
        """
        if not ids:
            return []

        col_name = collection_name or self.default_collection
        collection = self.get_or_create_collection(name=col_name)

        result = collection.get(
            ids=ids,
            include=["embeddings", "documents", "metadatas"],
        )

        records: List[Dict[str, Any]] = []
        found_ids = result.get("ids", [])
        embeddings = result.get("embeddings")
        documents = result.get("documents") or []
        metadatas = result.get("metadatas") or []

        for i, rec_id in enumerate(found_ids):
            vec = embeddings[i] if embeddings is not None and len(embeddings) > i else []
            doc = documents[i] if i < len(documents) else ""
            meta = metadatas[i] if i < len(metadatas) else {}

            records.append({
                "id": rec_id,
                "vector": list(vec) if hasattr(vec, "__iter__") else vec,
                "vector_length": len(vec) if vec is not None else 0,
                "text": doc,
                "metadata": meta,
            })

        return records

    def query_similar(
        self,
        query_vector: List[float],
        top_k: int = 4,
        filter_metadata: Optional[Dict[str, Any]] = None,
        collection_name: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Perform semantic nearest-neighbor similarity search on stored vectors.

        Args:
            query_vector: Dense query embedding vector.
            top_k: Number of nearest neighbors to return.
            filter_metadata: Optional metadata filter dict for filtered search.
            collection_name: Optional collection name.

        Returns:
            List of matching records ordered by similarity score.
        """
        col_name = collection_name or self.default_collection
        collection = self.get_or_create_collection(name=col_name)
        target_dim = self._collections.get(col_name, {}).get("dimension", self.dimension)

        self.validate_vector_dimension(query_vector, expected_dim=target_dim)

        kwargs: Dict[str, Any] = {
            "query_embeddings": [query_vector],
            "n_results": top_k,
            "include": ["embeddings", "documents", "metadatas", "distances"],
        }
        if filter_metadata:
            kwargs["where"] = filter_metadata

        results = collection.query(**kwargs)

        hits: List[Dict[str, Any]] = []
        if not results or not results.get("ids") or not results["ids"][0]:
            return hits

        ids = results["ids"][0]
        distances = results.get("distances", [[]])[0]
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        embeddings = results.get("embeddings", [[]])[0]

        for i, hit_id in enumerate(ids):
            dist = distances[i] if i < len(distances) else 0.0
            doc = documents[i] if i < len(documents) else ""
            meta = metadatas[i] if i < len(metadatas) else {}
            vec = embeddings[i] if embeddings is not None and i < len(embeddings) else []

            # For cosine distance: cosine_similarity = 1.0 - distance
            similarity = round(1.0 - dist, 6)

            hits.append({
                "id": hit_id,
                "similarity": similarity,
                "distance": round(dist, 6),
                "text": doc,
                "metadata": meta,
                "vector_length": len(vec) if vec is not None else 0,
            })

        return hits

    def count(self, collection_name: Optional[str] = None) -> int:
        """Return the number of items stored in the collection."""
        col_name = collection_name or self.default_collection
        collection = self.get_or_create_collection(name=col_name)
        return collection.count()

    def delete_collection(self, name: Optional[str] = None) -> None:
        """Delete a collection by name."""
        col_name = name or self.default_collection
        client = self.get_client()
        try:
            client.delete_collection(name=col_name)
            if col_name in self._collections:
                del self._collections[col_name]
        except Exception as e:
            logger.warning("Could not delete collection %s: %s", col_name, e)

    def list_collections(self) -> List[str]:
        """List all collection names in the vector database."""
        client = self.get_client()
        cols = client.list_collections()
        # Handle both list of strings or list of collection objects
        return [c.name if hasattr(c, "name") else str(c) for c in cols]
