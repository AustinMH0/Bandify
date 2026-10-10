const STORAGE_KEY = "groovonomy_session";

// After Spotify sign-in the API sends the browser back here with "#session=<token>"
export function captureSessionFromUrl(): void {
  const params = new URLSearchParams(window.location.hash.replace(/^#/, ""));
  const session = params.get("session");
  const loginError = params.get("login_error");
  if (!session && !loginError) return;

  if (session) {
    sessionStorage.setItem(STORAGE_KEY, session);
  } else {
    console.error("Spotify sign-in failed:", loginError);
  }
  // Keep the token out of the address bar and browser history
  window.history.replaceState(null, "", window.location.pathname + window.location.search);
}

export function hasSession(): boolean {
  return sessionStorage.getItem(STORAGE_KEY) !== null;
}

export function clearSession(): void {
  sessionStorage.removeItem(STORAGE_KEY);
}

export function authHeaders(): Record<string, string> {
  const session = sessionStorage.getItem(STORAGE_KEY);
  return session ? { Authorization: `Bearer ${session}` } : {};
}
