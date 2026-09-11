"""
Retrieval service for PolicyPilot RAG Assistant.

Responsibilities:
- Generate query embeddings
- Load document embeddings
- Retrieve relevant chunks
- Apply metadata filters
- Support hybrid vector + keyword search
- Provide compatibility methods for existing API/tests
- Evaluate retrieval quality
"""

from __future__ import annotations

import json
import logging
import re
import hashlib
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from src.services.embedding_service import EmbeddingService
from src.services.document_service import DocumentService

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DEFAULT_CACHE_FILE = (
    PROJECT_ROOT
    / "outputs"
    / "embedded_chunks.json"
)


def generate_deterministic_vector(text: str, dim: int = 1536) -> List[float]:
    """Compatibility helper using the same fallback as EmbeddingService."""
    service = EmbeddingService()
    if dim != service.DIMENSION:
        vector = service._offline_embedding(text)
        return vector[:dim] + [0.0] * max(0, dim - len(vector))
    return service._offline_embedding(text)


_deterministic_embedding = generate_deterministic_vector


class RetrievalService:
    """
    Single retrieval implementation used throughout PolicyPilot.
    """

    def __init__(
        self,
        embedding_service: Optional[EmbeddingService] = None,
        cache_file: Optional[Path | str] = None,
        vector_service: Optional[Any] = None,
        default_collection: str = "rag_chunks",
        dimension: int = 1536,
        embedding_fn: Optional[Any] = None,
    ):

        self.embedding_service = (
            embedding_service
            if embedding_service is not None
            else EmbeddingService()
        )

        self.cache_file = (
            Path(cache_file)
            if cache_file
            else DEFAULT_CACHE_FILE
        )
        self.vector_service = vector_service
        self.default_collection = default_collection
        self.dimension = dimension
        self.embedding_fn = embedding_fn

        self._vector_store_cache: Optional[
            Dict[str, Any]
        ] = None

    # =====================================================
    # EMBEDDING
    # =====================================================

    def embed_query(
        self,
        query: str,
    ) -> List[float]:
        """
        Generate a query embedding using the same
        EmbeddingService used for document embeddings.
        """

        if not query or not query.strip():
            raise ValueError(
                "Query string cannot be empty."
            )

        try:
            if self.embedding_fn is not None:
                vector = self.embedding_fn(query)
            elif hasattr(self.embedding_service, "generate_embedding"):
                vector = self.embedding_service.generate_embedding(query)
            elif hasattr(self.embedding_service, "embed_query"):
                vector = self.embedding_service.embed_query(query)
            else:
                vector = _deterministic_embedding(query)

            if not isinstance(vector, list):
                vector = list(vector)

            if not vector:
                raise ValueError(
                    "Embedding service returned an empty vector."
                )
            if len(vector) != self.dimension:
                raise ValueError(
                    f"Custom embedding_fn returned dimension {len(vector)}; expected {self.dimension}"
                )

            return vector

        except Exception as exc:
            if self.embedding_fn is not None:
                raise
            logger.warning(
                "Query embedding API unavailable (%s); using local embedding.",
                exc,
            )
            return _deterministic_embedding(query, getattr(self, "dimension", 1536))

    # =====================================================
    # LOAD VECTOR STORE
    # =====================================================

    def load_vector_store(
        self,
        force_reload: bool = False,
    ) -> Dict[str, Any]:
        """
        Load pre-generated embeddings from cache.

        If the cache does not exist, documents are loaded,
        chunked and embedded automatically.
        """

        if (
            self._vector_store_cache is not None
            and not force_reload
        ):
            return self._vector_store_cache

        # -------------------------------------------------
        # Existing cache
        # -------------------------------------------------

        if self.cache_file.exists():

            try:

                with open(
                    self.cache_file,
                    "r",
                    encoding="utf-8",
                ) as file:

                    store = json.load(file)

                if isinstance(store, dict) and store:

                    logger.info(
                        "Loaded %d chunks from %s",
                        len(store),
                        self.cache_file,
                    )

                    self._vector_store_cache = store

                    return store

            except Exception as exc:

                logger.warning(
                    "Could not load embedding cache: %s",
                    exc,
                )

        # -------------------------------------------------
        # Generate embeddings from documents
        # -------------------------------------------------

        logger.info(
            "Embedding cache unavailable. "
            "Building vector store from documents."
        )

        document_service = DocumentService()

        data_dir = (
            PROJECT_ROOT
            / "data"
        )

        chunks = (
            document_service
            .load_and_chunk_documents(
                data_dir=str(data_dir)
            )
        )

        store: Dict[str, Any] = {}

        if not chunks:

            logger.warning(
                "No document chunks found in %s",
                data_dir,
            )

            self._vector_store_cache = {}

            return {}

        texts = []

        for chunk in chunks:

            text = (
                chunk.get("text")
                or chunk.get("content")
                or ""
            )

            texts.append(text)

        try:
            if hasattr(self.embedding_service, "generate_batch_embeddings"):
                embeddings, _, _ = self.embedding_service.generate_batch_embeddings(texts)
            elif hasattr(self.embedding_service, "embed_texts"):
                embeddings = self.embedding_service.embed_texts(texts)
            else:
                embeddings = [_deterministic_embedding(text) for text in texts]

        except Exception as exc:
            logger.warning("Document embedding API unavailable (%s); using local embeddings.", exc)
            embeddings = [_deterministic_embedding(text) for text in texts]

        if len(embeddings) != len(chunks):

            raise RuntimeError(
                "Number of embeddings does not match "
                "number of document chunks."
            )

        # -------------------------------------------------
        # Build store
        # -------------------------------------------------

        for index, (
            chunk,
            embedding,
        ) in enumerate(
            zip(chunks, embeddings)
        ):

            chunk_id = (
                chunk.get(
                    "chunk_id"
                )
                or f"chunk_{index}"
            )

            source = chunk.get(
                "source",
                "unknown",
            )

            content = (
                chunk.get("text")
                or chunk.get("content")
                or ""
            )

            chunk_index = chunk.get(
                "index",
                index,
            )

            document_type = (
                Path(source)
                .suffix
                .lstrip(".")
            )

            store[chunk_id] = {

                "chunk_id": chunk_id,

                "source": source,

                "content": content,

                "embedding": embedding,

                "vector_dim": len(
                    embedding
                ),

                "chunk_index": chunk_index,

                "doc_type": document_type,

                "token_count": chunk.get(
                    "token_count",
                    0,
                ),

                "start_token": chunk.get(
                    "start_token",
                    0,
                ),

                "end_token": chunk.get(
                    "end_token",
                    0,
                ),

                "metadata": {
                    "source": source,
                    "chunk_index": chunk_index,
                    "token_count": chunk.get(
                        "token_count",
                        0,
                    ),
                    "start_token": chunk.get(
                        "start_token",
                        0,
                    ),
                    "end_token": chunk.get(
                        "end_token",
                        0,
                    ),
                    "doc_type": document_type,
                },
            }

        self._vector_store_cache = store

        return store

    # =====================================================
    # METADATA FILTER
    # =====================================================

    @staticmethod
    def _matches_metadata_filter(
        item: Dict[str, Any],
        metadata_filter: Optional[
            Dict[str, Any]
        ],
    ) -> bool:
        """
        Return True if a chunk matches all metadata filters.
        """

        if not metadata_filter:
            return True

        metadata = item.get(
            "metadata"
        )

        if not isinstance(
            metadata,
            dict,
        ):
            metadata = {}

        for (
            key,
            expected,
        ) in metadata_filter.items():

            actual = item.get(key)

            if actual is None:
                actual = metadata.get(key)

            # Derive doc_type from source
            if (
                actual is None
                and key == "doc_type"
            ):

                source = (
                    item.get("source")
                    or metadata.get("source")
                )

                if source:
                    actual = (
                        Path(source)
                        .suffix
                        .lstrip(".")
                    )

            if actual is None:
                return False

            # Multiple accepted values
            if isinstance(
                expected,
                (
                    list,
                    tuple,
                    set,
                ),
            ):

                expected_values = {
                    str(value).lower()
                    for value in expected
                }

                if (
                    str(actual).lower()
                    not in expected_values
                ):
                    return False

            else:

                if (
                    str(actual).lower()
                    != str(expected).lower()
                ):
                    return False

        return True

    # =====================================================
    # KEYWORD SCORE
    # =====================================================

    @staticmethod
    def _calculate_keyword_score(
        query: str,
        content: str,
        keywords: Optional[
            List[str]
        ] = None,
    ) -> float:
        """
        Calculate lexical similarity between query and content.
        """

        if (
            not query
            or not content
        ):
            return 0.0

        stop_words = {
            "a", "an", "and", "are", "can", "do", "for", "how", "i",
            "is", "me", "of", "our", "please", "policy", "policies",
            "the", "to", "what", "when", "where", "which", "who", "why",
            "you",
        }

        def terms(value: str) -> set[str]:
            return {
                word
                for word in re.findall(r"\b\w+\b", value.lower())
                if word not in stop_words and len(word) > 2
            }

        query_words = terms(query)
        content_words = terms(content)

        if not query_words:
            return 0.0

        overlap = (
            query_words
            & content_words
        )

        overlap_score = (
            len(overlap)
            / len(query_words)
        )

        # Explicit keywords get additional weight
        target_terms = keywords if keywords else list(query_words)

        keyword_boost = 0.0

        content_lower = content.lower()

        for term in target_terms:

            term = str(term).lower().strip()

            if (
                term
                and term in content_lower
            ):
                keyword_boost += 0.15

        return round(
            min(
                1.0,
                overlap_score
                + keyword_boost,
            ),
            4,
        )

    # =====================================================
    # MAIN SEARCH
    # =====================================================

    def search(
        self,
        query: str,
        top_k: int = 3,
        metadata_filter: Optional[
            Dict[str, Any]
        ] = None,
        hybrid: bool = False,
        alpha: float = 0.7,
        keywords: Optional[
            List[str]
        ] = None,
        vector_store: Optional[
            Dict[str, Any]
        ] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search the local vector store.

        This is the main low-level retrieval method.
        """

        if top_k <= 0:
            raise ValueError(
                "top_k must be greater than zero."
            )

        if (
            not query
            or not query.strip()
        ):
            return []

        # -------------------------------------------------
        # Query embedding
        # -------------------------------------------------

        query_vector = self.embed_query(
            query
        )

        # -------------------------------------------------
        # Vector store
        # -------------------------------------------------
        if self.vector_service is not None:
            collection = self.vector_service.get_or_create_collection(
                name=self.default_collection, dimension=self.dimension
            )
            query_result = collection.query(
                query_embeddings=[query_vector],
                n_results=top_k,
                where=metadata_filter or None,
            )
            results = []
            ids = query_result.get("ids", [[]])[0]
            docs = query_result.get("documents", [[]])[0]
            metas = query_result.get("metadatas", [[]])[0]
            distances = query_result.get("distances", [[]])[0]
            for index, item_id in enumerate(ids):
                metadata = metas[index] or {}
                content = docs[index] or ""
                distance = float(distances[index]) if distances else 0.0
                score = max(0.0, 1.0 - distance)
                results.append({
                    "id": item_id, "chunk_id": item_id, "score": score,
                    "distance": distance, "source": metadata.get("source", "unknown"),
                    "chunk_index": metadata.get("chunk_index", 0),
                    "content": content, "text": content, "metadata": metadata,
                })
            for rank, result in enumerate(results, start=1):
                result["rank"] = rank
            return results

        store = (
            vector_store
            if vector_store is not None
            else self.load_vector_store()
        )

        if not store:

            logger.warning(
                "Vector store is empty."
            )

            return []

        results: List[
            Dict[str, Any]
        ] = []

        # -------------------------------------------------
        # Similarity search
        # -------------------------------------------------

        for item_id, item in store.items():

            if not isinstance(
                item,
                dict,
            ):
                continue

            # Metadata filtering
            if (
                metadata_filter
                and not self._matches_metadata_filter(
                    item,
                    metadata_filter,
                )
            ):
                continue

            embedding = item.get(
                "embedding"
            )

            if not isinstance(
                embedding,
                list,
            ):
                continue

            if (
                len(embedding)
                != len(query_vector)
            ):
                logger.warning(
                    "Skipping %s because "
                    "embedding dimensions differ.",
                    item_id,
                )
                continue

            try:

                vector_score = float(
                    self.embedding_service
                    .cosine_similarity(
                        query_vector,
                        embedding,
                    )
                )

            except Exception as exc:

                logger.warning(
                    "Similarity calculation failed for %s: %s",
                    item_id,
                    exc,
                )

                continue

            content = (
                item.get("content")
                or item.get("text")
                or ""
            )

            source = item.get(
                "source",
                "unknown",
            )

            chunk_index = item.get(
                "chunk_index",
                0,
            )

            # -------------------------------------------------
            # Hybrid score
            # -------------------------------------------------

            if hybrid:

                keyword_score = (
                    self._calculate_keyword_score(
                        query=query,
                        content=content,
                        keywords=keywords,
                    )
                )

                alpha = max(
                    0.0,
                    min(
                        1.0,
                        alpha,
                    ),
                )

                # A local hashed embedding can give unrelated documents a
                # non-zero score. Require at least one meaningful lexical
                # match so an unrelated policy is never presented as an
                # answer simply because it is the closest vector.
                if keyword_score <= 0.0:
                    continue

                final_score = (
                    alpha * max(0.0, vector_score)
                    + (1.0 - alpha) * keyword_score
                )

            else:

                keyword_score = 0.0

                final_score = max(
                    0.0,
                    vector_score,
                )

            # -------------------------------------------------
            # Metadata
            # -------------------------------------------------

            metadata = item.get(
                "metadata"
            )

            if not isinstance(
                metadata,
                dict,
            ):
                metadata = {}

            metadata = metadata.copy()

            metadata.setdefault(
                "source",
                source,
            )

            metadata.setdefault(
                "chunk_index",
                chunk_index,
            )

            metadata.setdefault(
                "doc_type",
                Path(source)
                .suffix
                .lstrip("."),
            )

            metadata.setdefault(
                "token_count",
                item.get(
                    "token_count",
                    0,
                ),
            )

            # -------------------------------------------------
            # Result
            # -------------------------------------------------

            results.append({

                "id": item_id,

                "chunk_id": item_id,

                "score": round(
                    float(final_score),
                    4,
                ),

                "vector_score": round(
                    float(vector_score),
                    4,
                ),

                "keyword_score": round(
                    float(keyword_score),
                    4,
                ),

                "distance": round(
                    1.0
                    - float(vector_score),
                    4,
                ),

                "source": source,

                "chunk_index": chunk_index,

                "content": content,

                "text": content,

                "metadata": metadata,
            })

        # -------------------------------------------------
        # Sort
        # -------------------------------------------------

        results.sort(
            key=lambda result: result[
                "score"
            ],
            reverse=True,
        )

        results = results[:top_k]

        # -------------------------------------------------
        # Rank
        # -------------------------------------------------

        for index, result in enumerate(
            results,
            start=1,
        ):
            result["rank"] = index

        return results

    # =====================================================
    # RETRIEVE
    # =====================================================

    def retrieve(
        self,
        query: str,
        k: int = 3,
        metadata_filter: Optional[
            Dict[str, Any]
        ] = None,
        min_score: Optional[
            float
        ] = None,
        collection_name: Optional[
            str
        ] = None,
    ) -> List[Dict[str, Any]]:
        """
        Main public retrieval method used by ResponseService.

        collection_name is accepted for compatibility.
        The current local implementation uses the embedding cache.
        """

        del collection_name

        if k <= 0:
            raise ValueError("k must be a positive integer")
        results = self.search(
            query=query,
            top_k=k,
            metadata_filter=metadata_filter,
        )

        if min_score is not None:

            results = [
                result
                for result in results
                if result["score"]
                >= min_score
            ]

            for index, result in enumerate(
                results,
                start=1,
            ):
                result["rank"] = index

        return results

    def retrieve_ranked_chunks(
        self,
        query: str,
        candidate_chunks: List[Dict[str, Any]],
        top_k: int = 4,
    ) -> List[Dict[str, Any]]:
        """Rank an explicit candidate list using the shared embedding logic."""
        if top_k <= 0:
            raise ValueError("top_k must be greater than zero")
        if not query or not query.strip() or not candidate_chunks:
            return []
        query_vector = self.embed_query(query)
        ranked: List[Dict[str, Any]] = []
        for index, chunk in enumerate(candidate_chunks):
            text = str(chunk.get("text") or chunk.get("content") or "")
            vector = chunk.get("embedding")
            if not isinstance(vector, list):
                vector = self.embedding_service.generate_embedding(text)
            if len(vector) != len(query_vector):
                continue
            score = self.embedding_service.cosine_similarity(query_vector, vector)
            result = dict(chunk)
            result.setdefault("id", result.get("chunk_id", f"chunk-{index}"))
            result.setdefault("chunk_id", result["id"])
            result["text"] = text
            result["content"] = text
            result["score"] = round(max(0.0, float(score)), 4)
            result.setdefault("source", (result.get("metadata") or {}).get("source", "unknown"))
            result.setdefault("chunk_index", (result.get("metadata") or {}).get("chunk_index", index))
            result.setdefault("metadata", {"source": result["source"], "chunk_index": result["chunk_index"]})
            ranked.append(result)
        ranked.sort(key=lambda item: item["score"], reverse=True)
        for rank, item in enumerate(ranked[:top_k], start=1):
            item["rank"] = rank
        return ranked[:top_k]

    # =====================================================
    # FILTERED SEARCH
    # =====================================================

    def search_filtered(
        self,
        query: str,
        metadata_filter: Dict[str, Any],
        top_k: int = 3,
        vector_store: Optional[
            Dict[str, Any]
        ] = None,
    ) -> List[Dict[str, Any]]:

        return self.search(
            query=query,
            top_k=top_k,
            metadata_filter=metadata_filter,
            vector_store=vector_store,
        )

    # =====================================================
    # HYBRID SEARCH
    # =====================================================

    def search_hybrid(
        self,
        query: str,
        metadata_filter: Optional[
            Dict[str, Any]
        ] = None,
        alpha: float = 0.7,
        keywords: Optional[
            List[str]
        ] = None,
        top_k: int = 3,
        vector_store: Optional[
            Dict[str, Any]
        ] = None,
    ) -> List[Dict[str, Any]]:

        return self.search(
            query=query,
            top_k=top_k,
            metadata_filter=metadata_filter,
            hybrid=True,
            alpha=alpha,
            keywords=keywords,
            vector_store=vector_store,
        )

    # =====================================================
    # COMPARE FILTERED / UNFILTERED
    # =====================================================

    def compare_filtered_vs_unfiltered(
        self,
        query: str,
        metadata_filter: Dict[str, Any],
        top_k: int = 3,
        vector_store: Optional[
            Dict[str, Any]
        ] = None,
    ) -> Dict[str, Any]:

        store = (
            vector_store
            if vector_store is not None
            else self.load_vector_store()
        )

        unfiltered = self.search(
            query=query,
            top_k=top_k,
            vector_store=store,
        )

        filtered = self.search_filtered(
            query=query,
            metadata_filter=metadata_filter,
            top_k=top_k,
            vector_store=store,
        )

        unfiltered_matches = sum(
            1
            for result in unfiltered
            if self._matches_metadata_filter(
                result,
                metadata_filter,
            )
        )

        filtered_matches = sum(
            1
            for result in filtered
            if self._matches_metadata_filter(
                result,
                metadata_filter,
            )
        )

        unfiltered_precision = (
            (
                unfiltered_matches
                / len(unfiltered)
            )
            * 100
            if unfiltered
            else 0.0
        )

        filtered_precision = (
            (
                filtered_matches
                / len(filtered)
            )
            * 100
            if filtered
            else 0.0
        )

        return {

            "query": query,

            "metadata_filter": metadata_filter,

            "top_k": top_k,

            "unfiltered_precision_percent":
                round(
                    unfiltered_precision,
                    2,
                ),

            "filtered_precision_percent":
                round(
                    filtered_precision,
                    2,
                ),

            "unfiltered_target_matches":
                f"{unfiltered_matches}/{len(unfiltered)}",

            "filtered_target_matches":
                f"{filtered_matches}/{len(filtered)}",

            "unfiltered_results":
                unfiltered,

            "filtered_results":
                filtered,
        }

    # =====================================================
    # COMPARE K
    # =====================================================

    def compare_k(
        self,
        query: str,
        k_values: Optional[
            List[int]
        ] = None,
        vector_store: Optional[
            Dict[str, Any]
        ] = None,
    ) -> Dict[str, Any]:

        if k_values is None:
            k_values = [2, 5]

        store = (
            vector_store
            if vector_store is not None
            else self.load_vector_store()
        )

        comparisons = {}

        for k in k_values:

            results = self.search(
                query=query,
                top_k=k,
                vector_store=store,
            )

            scores = [
                result["score"]
                for result in results
            ]

            comparisons[
                f"k_{k}"
            ] = {

                "k": k,

                "retrieved_count":
                    len(results),

                "max_score":
                    max(scores)
                    if scores
                    else 0.0,

                "min_score":
                    min(scores)
                    if scores
                    else 0.0,

                "results":
                    results,
            }

        return {

            "query": query,

            "k_values_evaluated":
                k_values,

            "comparisons":
                comparisons,
        }

    # =====================================================
    # EVALUATION
    # =====================================================

    def evaluate_setting(
        self,
        setting: Dict[str, Any],
        test_queries: List[
            Dict[str, Any]
        ],
        collection_name: Optional[
            str
        ] = None,
    ) -> List[Dict[str, Any]]:

        rows = []

        k = setting.get(
            "k",
            3,
        )

        metadata_filter = (
            setting.get("filter")
            if "filter" in setting
            else setting.get(
                "metadata_filter"
            )
        )

        min_score = setting.get(
            "min_score"
        )

        for item in test_queries:

            query = item["query"]

            expected_source = item[
                "expected_source"
            ]

            results = self.retrieve(
                query=query,
                k=k,
                metadata_filter=metadata_filter,
                min_score=min_score,
                collection_name=collection_name,
            )

            sources = [
                result.get(
                    "metadata",
                    {},
                ).get(
                    "source",
                    "",
                )
                for result in results
            ]

            hit = (
                expected_source
                in sources
            )

            top_1_hit = (
                bool(sources)
                and sources[0]
                == expected_source
            )

            rank = None

            reciprocal_rank = 0.0

            if hit:

                rank = (
                    sources.index(
                        expected_source
                    )
                    + 1
                )

                reciprocal_rank = (
                    1.0
                    / rank
                )

            rows.append({

                "query": query,

                "expected_source":
                    expected_source,

                "returned_sources":
                    sources,

                "returned_count":
                    len(results),

                "hit":
                    hit,

                "top_1_hit":
                    top_1_hit,

                "rank":
                    rank,

                "reciprocal_rank":
                    reciprocal_rank,

                "results":
                    results,
            })

        return rows

    # =====================================================
    # METRICS
    # =====================================================

    @staticmethod
    def compute_metrics(
        evaluation_rows: List[
            Dict[str, Any]
        ],
    ) -> Dict[str, Any]:

        if not evaluation_rows:

            return {

                "total_queries": 0,

                "hits": 0,

                "hit_rate": 0.0,

                "top_1_hits": 0,

                "top_1_hit_rate": 0.0,

                "mrr": 0.0,

                "avg_returned_chunks": 0.0,
            }

        total = len(
            evaluation_rows
        )

        hits = sum(
            1
            for row in evaluation_rows
            if row.get("hit")
        )

        top_1_hits = sum(
            1
            for row in evaluation_rows
            if row.get("top_1_hit")
        )

        mrr_sum = sum(
            row.get(
                "reciprocal_rank",
                0.0,
            )
            for row in evaluation_rows
        )

        total_chunks = sum(
            row.get(
                "returned_count",
                0,
            )
            for row in evaluation_rows
        )

        return {

            "total_queries":
                total,

            "hits":
                hits,

            "hit_rate":
                round(
                    hits / total,
                    4,
                ),

            "top_1_hits":
                top_1_hits,

            "top_1_hit_rate":
                round(
                    top_1_hits / total,
                    4,
                ),

            "mrr":
                round(
                    mrr_sum / total,
                    4,
                ),

            "avg_returned_chunks":
                round(
                    total_chunks / total,
                    2,
                ),
        }

    # =====================================================
    # ALL EVALUATIONS
    # =====================================================

    def evaluate_all_settings(
        self,
        settings: List[
            Dict[str, Any]
        ],
        test_queries: List[
            Dict[str, Any]
        ],
        collection_name: Optional[
            str
        ] = None,
    ) -> List[Dict[str, Any]]:

        summary = []

        for setting in settings:

            rows = self.evaluate_setting(
                setting=setting,
                test_queries=test_queries,
                collection_name=collection_name,
            )

            metrics = self.compute_metrics(
                rows
            )

            summary.append({

                "setting":
                    setting.get(
                        "name",
                        "unnamed",
                    ),

                "config": {

                    "k":
                        setting.get(
                            "k",
                            3,
                        ),

                    "filter":
                        setting.get(
                            "filter"
                        )
                        or setting.get(
                            "metadata_filter"
                        ),

                    "min_score":
                        setting.get(
                            "min_score",
                            0.0,
                        ),
                },

                "hit_rate":
                    metrics[
                        "hit_rate"
                    ],

                "top_1_hit_rate":
                    metrics[
                        "top_1_hit_rate"
                    ],

                "mrr":
                    metrics[
                        "mrr"
                    ],

                "avg_returned_chunks":
                    metrics[
                        "avg_returned_chunks"
                    ],

                "metrics":
                    metrics,

                "details":
                    rows,
            })

        return summary