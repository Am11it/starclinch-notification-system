// Tiny helper around fetch: adds the token and turns errors into readable messages.
const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export function getToken() {
  return localStorage.getItem("token");
}

export function setToken(token) {
  if (token) localStorage.setItem("token", token);
  else localStorage.removeItem("token");
}

export async function api(path, { method = "GET", body } = {}) {
  const headers = { "Content-Type": "application/json" };
  if (getToken()) headers.Authorization = `Token ${getToken()}`;

  const response = await fetch(`${API_URL}/api${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });
  const data = response.status === 204 ? {} : await response.json().catch(() => ({}));

  if (!response.ok) {
    // DRF errors look like {"error": ".."}, {"detail": ".."} or {"field": [".."]}
    const message =
      data.error || data.detail || Object.entries(data).map(([k, v]) => `${k}: ${v}`).join(", ");
    throw new Error(message || `Request failed (${response.status})`);
  }
  return data;
}
