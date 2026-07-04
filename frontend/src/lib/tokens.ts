const ACCESS_KEY = "deskflow.access";
const REFRESH_KEY = "deskflow.refresh";

// localStorage only exists in the browser; during prerender these are no-ops.
const storage = () => (typeof window === "undefined" ? null : window.localStorage);

export function getAccessToken(): string | null {
  return storage()?.getItem(ACCESS_KEY) ?? null;
}

export function getRefreshToken(): string | null {
  return storage()?.getItem(REFRESH_KEY) ?? null;
}

export function setTokens(access: string, refresh?: string) {
  storage()?.setItem(ACCESS_KEY, access);
  if (refresh) storage()?.setItem(REFRESH_KEY, refresh);
}

export function clearTokens() {
  storage()?.removeItem(ACCESS_KEY);
  storage()?.removeItem(REFRESH_KEY);
}
