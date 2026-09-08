import { test, describe, beforeEach, afterEach } from "node:test";
import assert from "node:assert";
import { getStreamUrl, streamQuestion } from "../src/lib/api.js";

describe("Frontend Streaming API Helper & SSE Tests", () => {
  let originalFetch;

  beforeEach(() => {
    originalFetch = globalThis.fetch;
  });

  afterEach(() => {
    globalThis.fetch = originalFetch;
    delete process.env.NEXT_PUBLIC_RAG_API_URL;
  });

  test("getStreamUrl correctly derives /query/stream from NEXT_PUBLIC_RAG_API_URL", () => {
    // Default fallback
    assert.strictEqual(getStreamUrl(), "http://localhost:8000/query/stream");

    // Standard /query URL
    process.env.NEXT_PUBLIC_RAG_API_URL = "http://my-api-host:9000/query";
    assert.strictEqual(getStreamUrl(), "http://my-api-host:9000/query/stream");

    // Root domain without /query
    process.env.NEXT_PUBLIC_RAG_API_URL = "http://my-api-host:9000";
    assert.strictEqual(getStreamUrl(), "http://my-api-host:9000/query/stream");

    // Already stream URL
    process.env.NEXT_PUBLIC_RAG_API_URL = "http://my-api-host:9000/query/stream";
    assert.strictEqual(getStreamUrl(), "http://my-api-host:9000/query/stream");
  });

  test("empty question validation throws error before making fetch request", async () => {
    let fetchCalled = false;
    globalThis.fetch = async () => {
      fetchCalled = true;
      return {};
    };

    await assert.rejects(
      async () => await streamQuestion(""),
      {
        name: "Error",
        message: "Question cannot be empty.",
      }
    );

    assert.strictEqual(fetchCalled, false);
  });

  test("streamQuestion sends correct POST request to /query/stream", async () => {
    let capturedUrl;
    let capturedOptions;

    const encoder = new TextEncoder();
    const sseContent = [
      'data: {"type": "citations", "sources": [{"id": "source-1", "label": "[1]", "document": "policy.md", "chunk_id": "c1", "section": "Returns", "text": "30 days"}]}\n\n',
      'data: {"type": "token", "text": "Catalog "}\n\n',
      'data: {"type": "token", "text": "items."}\n\n',
      'data: {"type": "done"}\n\n',
    ];

    globalThis.fetch = async (url, options) => {
      capturedUrl = url;
      capturedOptions = options;

      let idx = 0;
      return {
        ok: true,
        status: 200,
        body: {
          getReader() {
            return {
              async read() {
                if (idx < sseContent.length) {
                  return { done: false, value: encoder.encode(sseContent[idx++]) };
                }
                return { done: true, value: undefined };
              },
            };
          },
        },
      };
    };

    let receivedTokens = [];
    let receivedCitations = [];
    let isDone = false;

    await streamQuestion("What is return policy?", {
      onToken: (tok) => receivedTokens.push(tok),
      onCitations: (srcs) => (receivedCitations = srcs),
      onDone: () => (isDone = true),
    });

    assert.strictEqual(capturedUrl, "http://localhost:8000/query/stream");
    assert.strictEqual(capturedOptions.method, "POST");
    assert.strictEqual(capturedOptions.headers["Content-Type"], "application/json");
    assert.strictEqual(capturedOptions.body, JSON.stringify({ question: "What is return policy?" }));

    assert.strictEqual(receivedCitations.length, 1);
    assert.strictEqual(receivedCitations[0].document, "policy.md");
    assert.strictEqual(receivedCitations[0].chunk_id, "c1");

    assert.deepStrictEqual(receivedTokens, ["Catalog ", "items."]);
    assert.strictEqual(isDone, true);
  });

  test("preserves received citations and partial answer upon stream interruption/error", async () => {
    const encoder = new TextEncoder();
    const sseContent = [
      'data: {"type": "citations", "sources": [{"id": "source-1", "label": "[1]", "document": "policy.md", "chunk_id": "c1", "section": "Returns", "text": "30 days"}]}\n\n',
      'data: {"type": "token", "text": "Partial "}\n\n',
      'data: {"type": "error", "message": "The answer stopped streaming. Please retry."}\n\n',
    ];

    globalThis.fetch = async () => {
      let idx = 0;
      return {
        ok: true,
        status: 200,
        body: {
          getReader() {
            return {
              async read() {
                if (idx < sseContent.length) {
                  return { done: false, value: encoder.encode(sseContent[idx++]) };
                }
                return { done: true, value: undefined };
              },
            };
          },
        },
      };
    };

    let tokensBuffer = "";
    let capturedSources = [];
    let errorMessage = null;

    await streamQuestion("Query interrupted?", {
      onToken: (t) => (tokensBuffer += t),
      onCitations: (srcs) => (capturedSources = srcs),
      onError: (msg) => (errorMessage = msg),
    });

    // Check partial tokens and citations preserved
    assert.strictEqual(tokensBuffer, "Partial ");
    assert.strictEqual(capturedSources.length, 1);
    assert.strictEqual(capturedSources[0].document, "policy.md");
    assert.strictEqual(errorMessage, "The answer stopped streaming. Please retry.");
  });

  test("handles network connection error gracefully", async () => {
    globalThis.fetch = async () => {
      throw new TypeError("Failed to fetch");
    };

    await assert.rejects(
      async () => await streamQuestion("Will this fail?"),
      (err) => {
        assert.ok(err.message.includes("Unable to connect to PolicyPilot RAG API server"));
        return true;
      }
    );
  });
});
