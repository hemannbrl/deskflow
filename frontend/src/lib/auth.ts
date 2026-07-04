import { api } from "./api";
import { clearTokens, setTokens } from "./tokens";

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
  clearTokens();
}
