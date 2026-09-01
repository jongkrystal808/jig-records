import { authSession, resetSession } from "@/appState";
import {
  rememberSessionExpiredReturnPath,
  SESSION_EXPIRED_EVENT,
  SESSION_EXPIRED_MESSAGE
} from "@/sessionExpiry";
import { pushToastOnce } from "@/toastState";
import { extractErrorMessage } from "@/utils/apiError";

export const API_ROOT = "/api/v2";

export class ApiRequestError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiRequestError";
    this.status = status;
  }
}

let sessionExpirationInProgress = false;

export function completeSessionExpirationRedirect(): void {
  sessionExpirationInProgress = false;
}

export function setOptionalParam(params: URLSearchParams, key: string, value: string | number | undefined | null): void {
  if (value === undefined || value === null || value === "") {
    return;
  }
  params.set(key, String(value));
}

export function setOptionalParams(
  params: URLSearchParams,
  key: string,
  value: string | number | Array<string | number> | undefined | null
): void {
  params.delete(key);
  const values = Array.isArray(value) ? value : [value];
  values.forEach((item) => {
    if (item !== undefined && item !== null && item !== "") params.append(key, String(item));
  });
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

function responseError(response: Response, body: string, withAuth: boolean): ApiRequestError {
  if (response.status === 401 && withAuth && (authSession.value || sessionExpirationInProgress)) {
    if (!sessionExpirationInProgress) {
      sessionExpirationInProgress = true;
      rememberSessionExpiredReturnPath();
      resetSession();
      pushToastOnce(SESSION_EXPIRED_MESSAGE, "warning", 5200);
      window.dispatchEvent(new CustomEvent(SESSION_EXPIRED_EVENT));
    }
    return new ApiRequestError(SESSION_EXPIRED_MESSAGE, response.status);
  }
  return new ApiRequestError(
    extractErrorMessage(body, `Request failed: ${response.status}`),
    response.status
  );
}

// Keep transport concerns centralized so domain clients only describe paths and payloads.
export async function request<T>(path: string, init?: RequestInit, withAuth = true): Promise<T> {
  const headers = buildHeaders(init, withAuth);
  const { headers: _ignoredHeaders, ...restInit } = init ?? {};
  const response = await fetch(`${API_ROOT}${path}`, {
    ...restInit,
    headers
  });

  const body = await response.text();

  if (!response.ok) {
    throw responseError(response, body, withAuth);
  }

  if (response.status === 204 || !body) {
    return undefined as T;
  }

  return JSON.parse(body) as T;
}

export async function requestText(path: string, init?: RequestInit, withAuth = true): Promise<string> {
  const headers = buildHeaders(init, withAuth);
  const { headers: _ignoredHeaders, ...restInit } = init ?? {};
  const response = await fetch(`${API_ROOT}${path}`, {
    ...restInit,
    headers
  });
  const body = await response.text();
  if (!response.ok) {
    throw responseError(response, body, withAuth);
  }
  return body;
}

export async function requestBlob(path: string, init?: RequestInit, withAuth = true): Promise<{
  blob: Blob;
  filename: string | null;
  rowCount: number | null;
  columnCount: number | null;
}> {
  const headers = buildHeaders(init, withAuth);
  const { headers: _ignoredHeaders, ...restInit } = init ?? {};
  const response = await fetch(`${API_ROOT}${path}`, {
    ...restInit,
    headers
  });
  if (!response.ok) {
    const body = await response.text();
    throw responseError(response, body, withAuth);
  }
  const contentDisposition = response.headers.get("Content-Disposition");
  const filenameMatch = contentDisposition?.match(/filename="?([^"]+)"?/i);
  const rowCountHeader = response.headers.get("X-Export-Row-Count");
  const columnCountHeader = response.headers.get("X-Export-Column-Count");
  return {
    blob: await response.blob(),
    filename: filenameMatch?.[1] ?? null,
    rowCount: rowCountHeader !== null && Number.isFinite(Number(rowCountHeader))
      ? Number(rowCountHeader)
      : null,
    columnCount: columnCountHeader !== null && Number.isFinite(Number(columnCountHeader))
      ? Number(columnCountHeader)
      : null
  };
}
