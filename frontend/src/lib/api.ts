import { clearTokens, getAccessToken, getRefreshToken, setTokens } from "./tokens";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

/** A non-2xx response; `data` is the DRF error body ({detail} or field errors). */
export class ApiError extends Error {
  status: number;
  data: unknown;

  constructor(status: number, data: unknown) {
    super(ApiError.detailOf(data) ?? `Request failed (${status})`);
    this.status = status;
    this.data = data;
  }

  private static detailOf(data: unknown): string | null {
    if (data && typeof data === "object" && "detail" in data) {
      return String((data as { detail: unknown }).detail);
    }
    return null;
  }

  /** First message for a serializer field error, e.g. fieldError("username"). */
  fieldError(field: string): string | null {
    if (this.data && typeof this.data === "object" && field in this.data) {
      const value = (this.data as Record<string, unknown>)[field];
      if (Array.isArray(value) && value.length > 0) return String(value[0]);
    }
    return null;
  }
}

async function refreshAccessToken(): Promise<boolean> {
  const refresh = getRefreshToken();
  if (!refresh) return false;
  const res = await fetch(`${BASE_URL}/api/auth/token/refresh/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh }),
  });
  if (!res.ok) return false;
  const data: { access: string } = await res.json();
  setTokens(data.access);
  return true;
}

/** JSON fetch against the API: attaches the JWT, refreshes once on 401. */
export async function api<T>(
  path: string,
  options: RequestInit = {},
  retryOn401 = true,
): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string> | undefined),
  };
  const access = getAccessToken();
  if (access) headers.Authorization = `Bearer ${access}`;

  const res = await fetch(`${BASE_URL}${path}`, { ...options, headers });

  if (res.status === 401 && retryOn401 && getRefreshToken()) {
    if (await refreshAccessToken()) return api<T>(path, options, false);
    clearTokens();
  }
  if (!res.ok) {
    throw new ApiError(res.status, await res.json().catch(() => null));
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}
