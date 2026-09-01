export const SESSION_EXPIRED_EVENT = "jig-record:session-expired";
export const SESSION_EXPIRED_MESSAGE = "登入已逾時，請重新登入。";
export const SESSION_EXPIRED_RETURN_KEY = "jig-record-session-expired-return";

function safeInternalPath(value: string): string | null {
  if (!value.startsWith("/") || value.startsWith("//")) {
    return null;
  }
  const pathname = value.split(/[?#]/, 1)[0];
  return pathname === "/login" ? null : value;
}

export function rememberSessionExpiredReturnPath(): string | null {
  if (typeof window === "undefined") return null;
  const returnPath = safeInternalPath(
    `${window.location.pathname}${window.location.search}${window.location.hash}`
  );
  if (returnPath) {
    window.sessionStorage.setItem(SESSION_EXPIRED_RETURN_KEY, returnPath);
  }
  return returnPath;
}

export function consumeSessionExpiredReturnPath(): string | null {
  if (typeof window === "undefined") return null;
  const stored = window.sessionStorage.getItem(SESSION_EXPIRED_RETURN_KEY);
  window.sessionStorage.removeItem(SESSION_EXPIRED_RETURN_KEY);
  return stored ? safeInternalPath(stored) : null;
}

export function clearSessionExpiredReturnPath(): void {
  if (typeof window !== "undefined") {
    window.sessionStorage.removeItem(SESSION_EXPIRED_RETURN_KEY);
  }
}
