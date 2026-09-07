/**
 * Frontend API helper to send user questions to the PolicyPilot backend RAG endpoint.
 *
 * @param {string} question - User question string.
 * @returns {Promise<{answer: string, citations: Object, sources: Array}>} Parsed JSON API response.
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
        if (errorData && errorData.error) {
          errorMsg = errorData.error;
        }
      } catch (e) {
        // Fallback if response payload is non-JSON
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
