import { test, describe, beforeEach, afterEach } from "node:test";
import assert from "node:assert";
import { askQuestion } from "../src/lib/api.js";

describe("Frontend askQuestion API Helper Tests", () => {
  let originalFetch;

  beforeEach(() => {
    originalFetch = globalThis.fetch;
  });

  afterEach(() => {
    globalThis.fetch = originalFetch;
    delete process.env.NEXT_PUBLIC_RAG_API_URL;
  });

  test("empty question validation throws error", async () => {
    await assert.rejects(
      async () => await askQuestion(""),
      {
        name: "Error",
        message: "Question cannot be empty.",
      }
    );

    await assert.rejects(
      async () => await askQuestion("   "),
      {
        name: "Error",
        message: "Question cannot be empty.",
      }
    );
  });

  test("POST /query request sent with correct headers, body, and method", async () => {
    let capturedUrl;
    let capturedOptions;

    globalThis.fetch = async (url, options) => {
      capturedUrl = url;
      capturedOptions = options;
      return {
        ok: true,
        status: 200,
        json: async () => ({
          answer: "Catalog items can be returned within 30 days. [1]",
          citations: {
            "[1]": {
              source: "RETURN_POLICY.md",
              chunk_id: "doc1:0",
              chunk_index: 0,
              section: "Return Window",
              text: "Catalog items can be returned within 30 days.",
            },
          },
          sources: [
            {
              marker: "[1]",
              source: "RETURN_POLICY.md",
              chunk_id: "doc1:0",
              chunk_index: 0,
              section: "Return Window",
              text: "Catalog items can be returned within 30 days.",
            },
          ],
        }),
      };
    };

    const result = await askQuestion("What is the return period?");

    assert.strictEqual(capturedUrl, "http://localhost:8000/query");
    assert.strictEqual(capturedOptions.method, "POST");
    assert.strictEqual(capturedOptions.headers["Content-Type"], "application/json");
    assert.strictEqual(capturedOptions.body, JSON.stringify({ question: "What is the return period?" }));

    assert.strictEqual(result.answer, "Catalog items can be returned within 30 days. [1]");
    assert.strictEqual(result.sources.length, 1);
    assert.strictEqual(result.sources[0].source, "RETURN_POLICY.md");
    assert.strictEqual(result.sources[0].chunk_id, "doc1:0");
    assert.strictEqual(result.sources[0].section, "Return Window");
  });

  test("respects NEXT_PUBLIC_RAG_API_URL environment variable", async () => {
    process.env.NEXT_PUBLIC_RAG_API_URL = "http://custom-api-domain:9000/api/query";
    let capturedUrl;

    globalThis.fetch = async (url) => {
      capturedUrl = url;
      return {
        ok: true,
        status: 200,
        json: async () => ({ answer: "OK", citations: {}, sources: [] }),
      };
    };

    await askQuestion("How long is shipping?");
    assert.strictEqual(capturedUrl, "http://custom-api-domain:9000/api/query");
  });

  test("handles empty sources response gracefully", async () => {
    globalThis.fetch = async () => ({
      ok: true,
      status: 200,
      json: async () => ({
        answer: "I don't have enough information in the provided context.",
        citations: {},
        sources: [],
      }),
    });

    const result = await askQuestion("Unrelated question?");
    assert.strictEqual(result.answer, "I don't have enough information in the provided context.");
    assert.deepStrictEqual(result.sources, []);
  });

  test("throws clear error message when API responds with HTTP 400 error", async () => {
    globalThis.fetch = async () => ({
      ok: false,
      status: 400,
      statusText: "Bad Request",
      json: async () => ({ error: "Question is required and cannot be empty." }),
    });

    await assert.rejects(
      async () => await askQuestion("invalid"),
      {
        name: "Error",
        message: "Question is required and cannot be empty.",
      }
    );
  });

  test("handles network fetch error gracefully", async () => {
    globalThis.fetch = async () => {
      const err = new TypeError("Failed to fetch");
      throw err;
    };

    await assert.rejects(
      async () => await askQuestion("What is the return period?"),
      (err) => {
        assert.ok(err.message.includes("Unable to connect to PolicyPilot RAG API server"));
        return true;
      }
    );
  });
});
