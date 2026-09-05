"""Retrieval Evaluation service for PolicyPilot."""

from typing import Any, Dict, Iterable, List, Optional, Set, Union
from src.services.retrieval_service import RetrievalService


def extract_chunk_id(chunk: Union[Dict[str, Any], str]) -> str:
    """Extract a unique string identifier from a chunk dictionary or string.

    Args:
        chunk: Chunk dictionary containing 'id', 'chunk_id', 'source' and 'chunk_index',
               or a string identifier directly.

    Returns:
        Extracted chunk identifier string.
    """
    if isinstance(chunk, str):
        return chunk
    if isinstance(chunk, dict):
        if "id" in chunk:
            return str(chunk["id"])
        if "chunk_id" in chunk:
            return str(chunk["chunk_id"])
        source = chunk.get("source", "")
        idx = chunk.get("chunk_index")
        if source and idx is not None:
            return f"{source}:{idx}"
        if "content" in chunk:
            return str(chunk["content"])
        if "text" in chunk:
            return str(chunk["text"])
    return str(chunk)


class RetrievalEvaluationService:
    """Service to evaluate document/chunk retrieval performance using Information Retrieval (IR) metrics."""

    def __init__(self, retrieval_service: Optional[RetrievalService] = None):
        """Initialize RetrievalEvaluationService.

        Args:
            retrieval_service: Optional RetrievalService instance for running candidate chunk retrieval.
        """
        self.retrieval_service = retrieval_service or RetrievalService()

    def calculate_metrics(
        self,
        retrieved_ids: List[str],
        relevant_chunk_ids: Iterable[str],
        top_k: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Calculate recall@k, precision@k, and hits for a set of retrieved and relevant chunk IDs.

        Formulas:
            recall = number of relevant chunks retrieved / total number of relevant chunks
            precision = number of relevant chunks retrieved / number of retrieved chunks

        Special handling:
            - If retrieved_ids is empty, precision is 0.0.
            - If relevant_chunk_ids is empty, recall is 0.0.

        Args:
            retrieved_ids: List of retrieved chunk ID strings (in ranked order).
            relevant_chunk_ids: Iterable (set or list) of ground-truth relevant chunk ID strings.
            top_k: Optional top-k cut-off threshold for retrieval.

        Returns:
            Dictionary containing:
                retrieved_ids, relevant_chunk_ids, hits, recall, recall@k, precision, precision@k
        """
        effective_retrieved = list(retrieved_ids)
        if top_k is not None and top_k > 0:
            effective_retrieved = effective_retrieved[:top_k]

        relevant_set: Set[str] = set(relevant_chunk_ids)
        retrieved_set: Set[str] = set(effective_retrieved)

        hits_set = retrieved_set & relevant_set
        hits = [cid for cid in effective_retrieved if cid in relevant_set]

        num_hits = len(hits_set)
        total_relevant = len(relevant_set)
        total_retrieved = len(effective_retrieved)

        # Handle empty relevant_chunk_ids safely
        if total_relevant == 0:
            recall = 0.0
        else:
            recall = num_hits / total_relevant

        # Handle empty retrieved_ids safely (precision should be 0)
        if total_retrieved == 0:
            precision = 0.0
        else:
            precision = num_hits / total_retrieved

        recall_val = round(float(recall), 4)
        precision_val = round(float(precision), 4)

        return {
            "retrieved_ids": effective_retrieved,
            "relevant_chunk_ids": relevant_set,
            "hits": hits,
            "hit_count": num_hits,
            "recall": recall_val,
            "recall@k": recall_val,
            "precision": precision_val,
            "precision@k": precision_val,
        }

    def evaluate_query(
        self,
        query: str,
        relevant_chunk_ids: Iterable[str],
        retrieved_chunks: Optional[List[Union[Dict[str, Any], str]]] = None,
        candidate_chunks: Optional[List[Dict[str, Any]]] = None,
        top_k: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Evaluate retrieval performance for a single labelled query.

        Args:
            query: User search query string.
            relevant_chunk_ids: Ground-truth relevant chunk IDs.
            retrieved_chunks: Pre-retrieved list of chunk dicts or chunk ID strings.
            candidate_chunks: Candidate chunk pool to run retrieval on if retrieved_chunks is None.
            top_k: Optional top-k cut-off threshold.

        Returns:
            Dictionary containing query metrics along with the original query string.
        """
        retrieved_ids: List[str] = []

        if retrieved_chunks is not None:
            retrieved_ids = [extract_chunk_id(c) for c in retrieved_chunks]
        elif candidate_chunks is not None and self.retrieval_service is not None:
            if hasattr(self.retrieval_service, "retrieve_ranked_chunks"):
                ranked = self.retrieval_service.retrieve_ranked_chunks(
                    query, candidate_chunks, top_k=top_k
                )
            elif hasattr(self.retrieval_service, "search"):
                ranked = self.retrieval_service.search(query, candidate_chunks)
            else:
                ranked = []
            retrieved_ids = [extract_chunk_id(c) for c in ranked]

        metrics = self.calculate_metrics(retrieved_ids, relevant_chunk_ids, top_k=top_k)
        metrics["query"] = query
        return metrics

    def evaluate_dataset(
        self,
        labelled_queries: List[Dict[str, Any]],
        candidate_chunks: Optional[List[Dict[str, Any]]] = None,
        top_k: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Evaluate aggregate retrieval performance across a dataset of labelled queries.

        Args:
            labelled_queries: List of query dicts, each containing:
                - 'query': str
                - 'relevant_chunk_ids': Iterable[str]
                - Optional 'retrieved_chunks' or 'retrieved_ids'
            candidate_chunks: Candidate chunk pool to perform retrieval on if query dict lacks pre-retrieved items.
            top_k: Optional top-k cut-off threshold.

        Returns:
            Dictionary containing:
                - number_of_queries / total_queries
                - average_recall / average_recall@k
                - average_precision / average_precision@k
                - query_results: list of per-query evaluation dicts
                - failed_queries: list of query failure details where recall < 1.0
        """
        if not labelled_queries:
            return {
                "number_of_queries": 0,
                "total_queries": 0,
                "average_recall": 0.0,
                "average_recall@k": 0.0,
                "average_precision": 0.0,
                "average_precision@k": 0.0,
                "query_results": [],
                "failed_queries": [],
            }

        query_results = []
        failed_queries = []

        for item in labelled_queries:
            query = item.get("query", "")
            relevant_chunk_ids = item.get("relevant_chunk_ids", set())
            retrieved_chunks = item.get("retrieved_chunks") or item.get("retrieved_ids")

            res = self.evaluate_query(
                query=query,
                relevant_chunk_ids=relevant_chunk_ids,
                retrieved_chunks=retrieved_chunks,
                candidate_chunks=candidate_chunks,
                top_k=top_k,
            )
            query_results.append(res)

            if res["recall"] < 1.0:
                failure_info = {
                    "query": query,
                    "relevant_chunk_ids": res["relevant_chunk_ids"],
                    "expected_chunk_ids": res["relevant_chunk_ids"],
                    "retrieved_chunk_ids": res["retrieved_ids"],
                    "retrieved_ids": res["retrieved_ids"],
                    "recall": res["recall"],
                    "recall@k": res["recall@k"],
                    "precision": res["precision"],
                    "precision@k": res["precision@k"],
                }
                failed_queries.append(failure_info)

        num_queries = len(query_results)
        avg_recall = sum(r["recall"] for r in query_results) / num_queries
        avg_precision = sum(r["precision"] for r in query_results) / num_queries

        avg_recall_val = round(float(avg_recall), 4)
        avg_precision_val = round(float(avg_precision), 4)

        return {
            "number_of_queries": num_queries,
            "total_queries": num_queries,
            "average_recall": avg_recall_val,
            "average_recall@k": avg_recall_val,
            "average_precision": avg_precision_val,
            "average_precision@k": avg_precision_val,
            "query_results": query_results,
            "failed_queries": failed_queries,
        }

    def inspect_failures(self, evaluation_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract failure inspection details from an aggregate evaluation result.

        Args:
            evaluation_result: Result dictionary returned by evaluate_dataset().

        Returns:
            List of dictionaries, each showing:
                - query (failed query)
                - expected/relevant chunk IDs
                - retrieved chunk IDs
                - recall
                - precision
        """
        return evaluation_result.get("failed_queries", [])
