import { api, BASE_URL } from "./api";
import { clearTokens, getRefreshToken, setTokens } from "./tokens";

export async function login(username: string, password: string) {
  const tokens = await api<{ access: string; refresh: string }>("/api/auth/token/", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });
  setTokens(tokens.access, tokens.refresh);
}

export async function register(username: string, email: string, password: string) {
  await api("/api/auth/register/", {
    method: "POST",
    body: JSON.stringify({ username, email, password }),
  });
  await login(username, password);
}

export function logout() {
  const refresh = getRefreshToken();
  if (refresh) {
    // Best-effort server-side revoke (blacklist the refresh token); never block
    // the local logout on it.
    void fetch(`${BASE_URL}/api/auth/logout/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh }),
    }).catch(() => {});
  }
  clearTokens();
}
