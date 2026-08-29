const API_URL = "http://127.0.0.1:8000";

export async function checkBackend() {
  const response = await fetch(`${API_URL}/health`);

  if (!response.ok) {
    throw new Error("Backend request failed");
  }

  return response.json();
}

export async function simulateCircuit(r1Resistance) {
  const response = await fetch(
    `${API_URL}/simulate-circuit`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        r1_resistance: r1Resistance,
      }),
    }
  );

  if (!response.ok) {
    throw new Error("Circuit simulation failed");
  }

  return response.json();
}

export async function getDemoCircuit() {
  const response = await fetch(
    `${API_URL}/demo-circuit`
  );

  if (!response.ok) {
    throw new Error("Circuit request failed");
  }

  return response.json();
}