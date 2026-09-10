from fastapi.testclient import TestClient

from src import api


client = TestClient(api.app)


class FakeRetrieval:
    def search(self, question, top_k):
        return [
            {
                "source": "policy.pdf",
                "score": 0.91,
                "chunk_index": 2,
                "content": "The policy answer.",
            }
        ]


class FakeResponse:
    model = "test-model"

    def generate(self, question, context_chunks):
        return {
            "generated_answer": "The policy answer. [Source: policy.pdf]",
            "context_chunks": context_chunks,
            "is_fallback": False,
        }


def test_query_returns_structured_grounded_response(monkeypatch):
    api.get_pipeline.cache_clear()
    monkeypatch.setattr(api, "get_pipeline", lambda: (FakeRetrieval(), FakeResponse()))

    response = client.post("/query", json={"question": "What is the policy?"})

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["answer"].startswith("The policy answer")
    assert body["sources"] == [{"document": "policy.pdf", "score": 0.91, "chunks": [2]}]
    assert body["metadata"]["retrieved_chunks"] == 1


def test_query_rejects_missing_question():
    response = client.post("/query", json={})

    assert response.status_code == 422


def test_query_rejects_blank_question(monkeypatch):
    response = client.post("/query", json={"question": "   "})

    assert response.status_code == 422


def test_query_returns_500_when_pipeline_fails(monkeypatch):
    def failing_pipeline():
        raise RuntimeError("provider unavailable")

    monkeypatch.setattr(api, "get_pipeline", failing_pipeline)

    response = client.post("/query", json={"question": "What is the policy?"})

    assert response.status_code == 500
    assert response.json()["detail"] == "The RAG pipeline could not process the question."
