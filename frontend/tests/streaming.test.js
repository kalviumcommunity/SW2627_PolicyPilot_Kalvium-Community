import test from "node:test";
import assert from "node:assert";
import { streamQuestion } from "../src/lib/api.js";

test("streamQuestion throws error for empty input", async () => {
  await assert.rejects(
    async () => {
      await streamQuestion("");
    },
    {
      name: "Error",
      message: "Question cannot be empty.",
    }
  );
});

test("streamQuestion parses SSE token, citations, and done events", async () => {
  const originalFetch = global.fetch;

  const ssePayload = [
    'data: {"type": "token", "text": "Hello "}\n\n',
    'data: {"type": "token", "text": "world!"}\n\n',
    'data: {"type": "citations", "sources": [{"id": "source-1", "citation_num": 1}]}\n\n',
    'data: {"type": "done"}\n\n',
  ];

  const stream = new ReadableStream({
    start(controller) {
      const encoder = new TextEncoder();
      for (const chunk of ssePayload) {
        controller.enqueue(encoder.encode(chunk));
      }
      controller.close();
    },
  });

  global.fetch = async (url, options) => {
    assert.strictEqual(url, "http://localhost:8000/query/stream");
    assert.strictEqual(options.method, "POST");
    return {
      ok: true,
      body: stream,
    };
  };

  const tokens = [];
  let sources = [];
  let isDone = false;

  try {
    await streamQuestion("Hello?", {
      onToken: (t) => tokens.push(t),
      onCitations: (s) => (sources = s),
      onDone: () => (isDone = true),
    });

    assert.strictEqual(tokens.join(""), "Hello world!");
    assert.strictEqual(sources.length, 1);
    assert.strictEqual(sources[0].id, "source-1");
    assert.strictEqual(isDone, true);
  } finally {
    global.fetch = originalFetch;
  }
});

test("streamQuestion handles SSE error events gracefully", async () => {
  const originalFetch = global.fetch;

  const ssePayload = [
    'data: {"type": "token", "text": "Partial text..."}\n\n',
    'data: {"type": "error", "message": "Stream interrupted"}\n\n',
  ];

  const stream = new ReadableStream({
    start(controller) {
      const encoder = new TextEncoder();
      for (const chunk of ssePayload) {
        controller.enqueue(encoder.encode(chunk));
      }
      controller.close();
    },
  });

  global.fetch = async () => ({
    ok: true,
    body: stream,
  });

  let errorMessage = "";

  try {
    await streamQuestion("Fail test", {
      onError: (msg) => {
        errorMessage = msg;
      },
    });

    assert.strictEqual(errorMessage, "Stream interrupted");
  } finally {
    global.fetch = originalFetch;
  }
});
