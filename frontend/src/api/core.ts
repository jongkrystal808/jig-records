import { authSession } from "@/appState";
import { extractErrorMessage } from "@/utils/apiError";

export const API_ROOT = "/api/v2";

export function setOptionalParam(params: URLSearchParams, key: string, value: string | number | undefined | null): void {
  if (value === undefined || value === null || value === "") {
    return;
  }
  params.set(key, String(value));
}

function buildHeaders(init?: RequestInit, withAuth = true): Headers {
  const headers = new Headers(init?.headers ?? {});
  if (!(init?.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  headers.set("Accept", "application/json, text/plain;q=0.9, */*;q=0.8");
  if (withAuth && authSession.value?.token && !headers.has("Authorization")) {
    headers.set("Authorization", `Bearer ${authSession.value.token}`);
  }
  return headers;
}

// Keep transport concerns centralized so domain clients only describe paths and payloads.
export async function request<T>(path: string, init?: RequestInit, withAuth = true): Promise<T> {
  const headers = buildHeaders(init, withAuth);
  const response = await fetch(`${API_ROOT}${path}`, {
    headers,
    ...init
  });

  const body = await response.text();

  if (!response.ok) {
    throw new Error(extractErrorMessage(body, `Request failed: ${response.status}`));
  }

  if (response.status === 204 || !body) {
    return undefined as T;
  }

  return JSON.parse(body) as T;
}

export async function requestText(path: string, init?: RequestInit, withAuth = true): Promise<string> {
  const headers = buildHeaders(init, withAuth);
  const response = await fetch(`${API_ROOT}${path}`, {
    headers,
    ...init
  });
  const body = await response.text();
  if (!response.ok) {
    throw new Error(extractErrorMessage(body, `Request failed: ${response.status}`));
  }
  return body;
}

export async function requestBlob(path: string, init?: RequestInit, withAuth = true): Promise<{ blob: Blob; filename: string | null }> {
  const headers = buildHeaders(init, withAuth);
  const response = await fetch(`${API_ROOT}${path}`, {
    headers,
    ...init
  });
  if (!response.ok) {
    const body = await response.text();
    throw new Error(extractErrorMessage(body, `Request failed: ${response.status}`));
  }
  const contentDisposition = response.headers.get("Content-Disposition");
  const filenameMatch = contentDisposition?.match(/filename="?([^"]+)"?/i);
  return {
    blob: await response.blob(),
    filename: filenameMatch?.[1] ?? null
  };
}
