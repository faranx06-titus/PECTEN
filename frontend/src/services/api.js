const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

async function requestError(response, fallback) {
  const payload = await response.json().catch(() => ({}));
  return new Error(payload.detail || fallback);
}

export async function checkBackend() {
  const response = await fetch(`${API_URL}/health`);

  if (!response.ok) {
    throw new Error("Backend request failed");
  }

  return response.json();
}

export async function simulateCircuit(circuitData) {
  const response = await fetch(
    `${API_URL}/simulate-circuit`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        circuit: circuitData,
      }),
    }
  );

  if (!response.ok) throw await requestError(response, "Circuit simulation failed");

  return response.json();
}

export async function analyzeCircuit(file, apiKey = null, question = "") {
  const formData = new FormData();

  formData.append("file", file);
  if (question) formData.append("question", question);

  let response;
  try {
    response = await fetch(`${API_URL}/analyze-circuit`, {
      method: "POST",
      body: formData,
      headers: apiKey ? { "X-API-Key": apiKey } : {},
    });
  } catch {
    throw new Error("Could not reach the PECTEN analysis server. Check that the backend is running, then try again.");
  }

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    const detail = typeof errorData.detail === "string" ? errorData.detail : "Circuit analysis failed.";
    if (response.status === 429 || /quota|rate limit|resource_exhausted/i.test(detail)) {
      throw new Error(detail || "Gemini's API limit was reached. Add a key with available quota in Settings or try again after the limit resets.");
    }
    if (response.status === 422 && /could not identify a circuit/i.test(detail)) {
      throw new Error(detail);
    }
    throw new Error(detail);
  }

  try {
    return await response.json();
  } catch {
    throw new Error("The analysis server returned an unreadable response. Try again, or choose a clearer crop.");
  }
}
