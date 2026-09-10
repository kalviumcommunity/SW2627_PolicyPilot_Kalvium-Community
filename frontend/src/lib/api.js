/**
 * Frontend API helper to send user questions to the PolicyPilot backend RAG endpoint.
 *
 * @param {string} question - User question string.
 * @returns {Promise<{answer: string, citations: Object, sources: Array, usage?: Object}>} Parsed JSON API response.
 * @throws {Error} Throws error with descriptive message if request is invalid or fails.
 */
export async function askQuestion(question) {
  if (!question || !question.trim()) {
    throw new Error("Question cannot be empty.");
  }

  const apiUrl =
    (typeof process !== "undefined" && process.env && process.env.NEXT_PUBLIC_RAG_API_URL) ||
    "http://localhost:8000/query";

  try {
    const response = await fetch(apiUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ question: question.trim() }),
    });

    if (!response.ok) {
      let errorMsg = `API request failed with status ${response.status}`;
      try {
        const errorData = await response.json();
        if (errorData) {
          errorMsg = errorData.error || errorData.detail || errorMsg;
        }
      } catch {
        // Keep the status-based message when the response is not JSON.
      }
      throw new Error(errorMsg);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    if (error.name === "TypeError" && error.message && error.message.toLowerCase().includes("fetch")) {
      throw new Error("Unable to connect to PolicyPilot RAG API server. Please check your backend connection.");
    }
    throw error;
  }
}

/**
 * Derives the /query/stream endpoint URL from NEXT_PUBLIC_RAG_API_URL environment variable.
 *
 * @returns {string} Fully qualified stream API URL.
 */
export function getStreamUrl() {
  const baseUrl =
    (typeof process !== "undefined" && process.env && process.env.NEXT_PUBLIC_RAG_API_URL) ||
    "http://localhost:8000/query";

  if (baseUrl.endsWith("/query/stream")) {
    return baseUrl;
  }
  if (baseUrl.endsWith("/query")) {
    return baseUrl.replace(/\/query$/, "/query/stream");
  }
  return baseUrl.replace(/\/$/, "") + "/query/stream";
}

/**
 * Frontend streaming helper to consume POST /query/stream Server-Sent Events.
 *
 * @param {string} question - User question string.
 * @param {Object} handlers - Callbacks for token, citations, done, error event handling.
 */
export async function streamQuestion(question, handlers = {}) {
  if (!question || !question.trim()) {
    throw new Error("Question cannot be empty.");
  }

  const { onToken, onCitations, onError, onDone, signal } = handlers;
  const streamUrl = getStreamUrl();

  let response;
  try {
    response = await fetch(streamUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ question: question.trim() }),
      signal,
    });
  } catch (error) {
    if (error.name === "TypeError" && error.message && error.message.toLowerCase().includes("fetch")) {
      throw new Error("Unable to connect to PolicyPilot RAG API server. Please check your backend connection.");
    }
    throw error;
  }

  if (!response.ok) {
    let errorMsg = `API request failed with status ${response.status}`;
    try {
      const errorData = await response.json();
      if (errorData) {
        errorMsg = errorData.error || errorData.detail || errorMsg;
      }
    } catch {
      // Keep the status-based message when the response is not JSON.
    }
    throw new Error(errorMsg);
  }

  if (!response.body) {
    throw new Error("Response body is not readable.");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder("utf-8");
  let buffer = "";

  const parseAndDispatch = (jsonStr) => {
    try {
      const data = JSON.parse(jsonStr);
      if (data.type === "token" && onToken) {
        onToken(data.text || "");
      } else if (data.type === "citations" && onCitations) {
        onCitations(data.sources || []);
      } else if (data.type === "done" && onDone) {
        onDone();
      } else if (data.type === "error" && onError) {
        onError(data.message || "The answer stopped streaming. Please retry.");
      }
    } catch (e) {
      // Ignore JSON parse errors for non-JSON lines
    }
  };

  const processChunk = (chunkText) => {
    buffer += chunkText;
    const parts = buffer.split("\n\n");
    buffer = parts.pop() || "";

    for (const part of parts) {
      const lines = part.split("\n");
      for (const line of lines) {
        const trimmed = line.trim();
        if (trimmed.startsWith("data:")) {
          const jsonStr = trimmed.slice(5).trim();
          if (jsonStr) {
            parseAndDispatch(jsonStr);
          }
        }
      }
    }
  };

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      const chunkText = decoder.decode(value, { stream: true });
      processChunk(chunkText);
    }

    if (buffer.trim()) {
      const lines = buffer.split("\n");
      for (const line of lines) {
        const trimmed = line.trim();
        if (trimmed.startsWith("data:")) {
          const jsonStr = trimmed.slice(5).trim();
          if (jsonStr) {
            parseAndDispatch(jsonStr);
          }
        }
      }
    }
  } catch (err) {
    if (onError) {
      onError("The answer stopped streaming. Please retry.");
    } else {
      throw err;
    }
  }
}
