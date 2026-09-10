"""Unit tests for VectorStoreService."""

import pytest
import tempfile
import shutil
import chromadb
from src.services.vector_store_service import VectorStoreService


@pytest.fixture
def temp_dir():
    """Fixture to provide a temporary directory for persistent client tests."""
    d = tempfile.mkdtemp()
    yield d
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def vector_service():
    """Fixture providing an ephemeral in-memory VectorStoreService for fast isolated tests."""
    client = chromadb.EphemeralClient()
    service = VectorStoreService(client=client, dimension=1536)
    yield service
    # Teardown: delete any collections created during test to ensure test isolation
    for col in client.list_collections():
        col_name = col.name if hasattr(col, "name") else str(col)
        try:
            client.delete_collection(col_name)
        except Exception:
            pass




def create_dummy_vector(dim=1536, seed=1.0):
    """Generate normalized dummy vector of given dimension."""
    raw = [(i + 1) * seed * 0.001 for i in range(dim)]
    norm = sum(x * x for x in raw) ** 0.5
    return [round(x / norm, 6) for x in raw]


def test_client_reachability_in_memory(vector_service):
    """Task 1: Verify vector database client is reachable in memory."""
    client = vector_service.get_client()
    assert client is not None
    assert vector_service.list_collections() == []


def test_client_reachability_persistent(temp_dir):
    """Task 1: Verify persistent vector database client initializes and persists directory."""
    service = VectorStoreService(persist_directory=temp_dir, in_memory=False)
    client = service.get_client()
    assert client is not None
    assert service.persist_directory == temp_dir


def test_create_collection_with_correct_dimension(vector_service):
    """Task 2: Verify creating a collection with 1536 dimensions and cosine metric."""
    collection = vector_service.get_or_create_collection(
        name="rag_chunks", dimension=1536, metric="cosine"
    )
    assert collection is not None
    assert collection.name == "rag_chunks"
    assert "rag_chunks" in vector_service.list_collections()


def test_dimension_validation_mismatch(vector_service):
    """Task 2: Verify dimension mismatch fails early with ValueError."""
    # Create 1536-dim collection
    vector_service.get_or_create_collection(name="rag_chunks", dimension=1536)

    invalid_dim_record = {
        "id": "bad-dim-record",
        "vector": [0.1, 0.2, 0.3],  # Length 3 instead of 1536
        "text": "Sample text",
        "metadata": {"source": "test.md"}
    }

    with pytest.raises(ValueError, match="Vector dimension mismatch"):
        vector_service.upsert_records([invalid_dim_record], collection_name="rag_chunks")


def test_insert_and_readback_single_record(vector_service):
    """Task 3 & 4: Insert a test record and read it back showing ID, vector length, text, metadata."""
    vector_service.get_or_create_collection(name="rag_chunks", dimension=1536)
    test_vector = create_dummy_vector(dim=1536, seed=42.0)

    test_record = {
        "id": "account-guide.md:0",
        "vector": test_vector,
        "text": "Password reset instructions for learner accounts.",
        "metadata": {
            "source": "account-guide.md",
            "chunk_index": 0,
            "section": "Account access",
        },
    }

    # Insert record
    upserted_ids = vector_service.upsert_records([test_record], collection_name="rag_chunks")
    assert upserted_ids == ["account-guide.md:0"]

    # Read back record
    stored = vector_service.get_record("account-guide.md:0", collection_name="rag_chunks")

    assert stored is not None
    assert stored["id"] == "account-guide.md:0"
    assert stored["vector_length"] == 1536
    assert len(stored["vector"]) == 1536
    assert stored["text"] == "Password reset instructions for learner accounts."
    assert stored["metadata"]["source"] == "account-guide.md"
    assert stored["metadata"]["chunk_index"] == 0
    assert stored["metadata"]["section"] == "Account access"


def test_upsert_record_helper(vector_service):
    """Task 4: Verify upsert_record helper method."""
    vector_service.get_or_create_collection(name="rag_chunks", dimension=1536)
    vec = create_dummy_vector(dim=1536)

    rec_id = vector_service.upsert_record(
        id="work_hours.md:0",
        vector=vec,
        text="Standard Working Hours: 8 hours per day.",
        metadata={"source": "work_hours.md", "chunk_index": 0},
    )
    assert rec_id == "work_hours.md:0"

    stored = vector_service.get_record("work_hours.md:0")
    assert stored is not None
    assert stored["id"] == "work_hours.md:0"
    assert stored["text"] == "Standard Working Hours: 8 hours per day."


def test_batch_upsert_and_readback(vector_service):
    """Task 4: Verify multiple records can be batch-inserted and read back."""
    records = [
        {
            "id": f"doc-{i}.md:0",
            "vector": create_dummy_vector(dim=1536, seed=float(i + 1)),
            "text": f"Content for document chunk {i}",
            "metadata": {"source": f"doc-{i}.md", "chunk_index": i},
        }
        for i in range(5)
    ]

    vector_service.upsert_records(records)
    assert vector_service.count() == 5

    read_records = vector_service.get_records([r["id"] for r in records])
    assert len(read_records) == 5
    for r in read_records:
        assert r["vector_length"] == 1536


def test_readback_nonexistent_returns_none(vector_service):
    """Verify that looking up a nonexistent ID returns None."""
    stored = vector_service.get_record("missing-id:999")
    assert stored is None


def test_schema_missing_required_fields(vector_service):
    """Task 3: Verify schema validation enforces 'id' and 'vector'."""
    with pytest.raises(ValueError, match="missing required 'id'"):
        vector_service.upsert_records([{"vector": [0.1] * 1536, "text": "missing id"}])

    with pytest.raises(ValueError, match="missing required vector"):
        vector_service.upsert_records([{"id": "valid-id", "text": "missing vector"}])


def test_query_similar_with_filtering(vector_service):
    """Verify semantic similarity query and metadata filtering."""
    vec1 = create_dummy_vector(dim=1536, seed=1.0)
    vec2 = create_dummy_vector(dim=1536, seed=2.0)
    vec3 = create_dummy_vector(dim=1536, seed=3.0)

    records = [
        {"id": "doc1:0", "vector": vec1, "text": "Account login password guide", "metadata": {"source": "account.md", "type": "guide"}},
        {"id": "doc2:0", "vector": vec2, "text": "Travel expense reimbursement guide", "metadata": {"source": "travel.pdf", "type": "policy"}},
        {"id": "doc3:0", "vector": vec3, "text": "Remote working guidelines", "metadata": {"source": "remote.md", "type": "policy"}},
    ]
    vector_service.upsert_records(records)

    # Query with vec1 should rank doc1:0 top
    hits = vector_service.query_similar(query_vector=vec1, top_k=3)
    assert len(hits) == 3
    assert hits[0]["id"] == "doc1:0"
    assert hits[0]["similarity"] > 0.99  # Identical vector

    # Query with filter on type == 'policy'
    filtered_hits = vector_service.query_similar(
        query_vector=vec1, top_k=3, filter_metadata={"type": "policy"}
    )
    assert len(filtered_hits) == 2
    assert all(h["metadata"]["type"] == "policy" for h in filtered_hits)


def test_delete_collection(vector_service):
    """Verify collection deletion."""
    vector_service.get_or_create_collection("temp_col", dimension=1536)
    assert "temp_col" in vector_service.list_collections()

    vector_service.delete_collection("temp_col")
    assert "temp_col" not in vector_service.list_collections()
