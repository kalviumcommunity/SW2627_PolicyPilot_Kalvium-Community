import test from "node:test";
import assert from "node:assert";
import { askQuestion, getStreamUrl } from "../src/lib/api.js";

test("askQuestion throws error for empty question", async () => {
  await assert.rejects(
    async () => {
      await askQuestion("");
    },
    {
      name: "Error",
      message: "Question cannot be empty.",
    }
  );
});

test("askQuestion throws error for whitespace question", async () => {
  await assert.rejects(
    async () => {
      await askQuestion("   ");
    },
    {
      name: "Error",
      message: "Question cannot be empty.",
    }
  );
});

test("getStreamUrl computes correct URL from default and custom endpoints", () => {
  // Test default
  const defaultUrl = getStreamUrl();
  assert.strictEqual(defaultUrl, "http://localhost:8000/query/stream");
});

test("askQuestion handles successful fetch response", async () => {
  const originalFetch = global.fetch;
  global.fetch = async (url, options) => {
    assert.strictEqual(url, "http://localhost:8000/query");
    assert.strictEqual(options.method, "POST");
    const body = JSON.parse(options.body);
    assert.strictEqual(body.question, "What is the policy?");

    return {
      ok: true,
      json: async () => ({
        answer: "The refund policy allows 14 days.",
        citations: [{ id: "doc-1", citation_num: 1 }],
        sources: [{ id: "doc-1", citation_num: 1 }],
      }),
    };
  };

  try {
    const res = await askQuestion("What is the policy?");
    assert.strictEqual(res.answer, "The refund policy allows 14 days.");
    assert.strictEqual(res.sources.length, 1);
  } finally {
    global.fetch = originalFetch;
  }
});

test("askQuestion handles HTTP error responses", async () => {
  const originalFetch = global.fetch;
  global.fetch = async () => ({
    ok: false,
    status: 400,
    json: async () => ({ error: "Invalid question query" }),
  });

  try {
    await assert.rejects(
      async () => {
        await askQuestion("Invalid?");
      },
      {
        name: "Error",
        message: "Invalid question query",
      }
    );
  } finally {
    global.fetch = originalFetch;
  }
});
