// @vitest-environment jsdom

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { authSession, selectedCustomerId } from "@/appState";
import {
  completeSessionExpirationRedirect,
  request,
  requestBlob,
  requestText
} from "@/api/core";
import {
  SESSION_EXPIRED_EVENT,
  SESSION_EXPIRED_MESSAGE,
  SESSION_EXPIRED_RETURN_KEY
} from "@/sessionExpiry";
import { toasts } from "@/toastState";
import type { AuthSession } from "@/types";

const activeSession: AuthSession = {
  mode: "user",
  user: null,
  display_name: "Admin",
  token: "expired-token",
  role: "admin"
};

beforeEach(() => {
  vi.useFakeTimers();
  completeSessionExpirationRedirect();
  window.sessionStorage.clear();
  window.history.replaceState({}, "", "/production/requirements?model_id=8#capacity");
  authSession.value = activeSession;
  selectedCustomerId.value = 20;
  window.sessionStorage.setItem("jig-record-session", JSON.stringify(activeSession));
  window.sessionStorage.setItem("jig-record-customer-id", "20");
  toasts.value = [];
});

afterEach(() => {
  vi.runOnlyPendingTimers();
  vi.useRealTimers();
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
  completeSessionExpirationRedirect();
  authSession.value = null;
  selectedCustomerId.value = null;
  window.sessionStorage.clear();
});

describe("API session expiry handling", () => {
  it("handles concurrent authenticated 401 responses only once across all transports", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation(() =>
        Promise.resolve(
          new Response(JSON.stringify({ error: { message: "token expired" } }), {
            status: 401,
            headers: { "Content-Type": "application/json" }
          })
        )
      )
    );
    const expiredEvents: Event[] = [];
    window.addEventListener(SESSION_EXPIRED_EVENT, (event) => expiredEvents.push(event), { once: true });

    const results = await Promise.allSettled([
      request("/master/customers"),
      requestText("/inventory/transactions/export"),
      requestBlob("/inventory/configuration-report/export")
    ]);

    expect(results.every((result) => result.status === "rejected")).toBe(true);
    for (const result of results) {
      if (result.status === "rejected") {
        expect(result.reason).toMatchObject({ status: 401, message: SESSION_EXPIRED_MESSAGE });
      }
    }
    expect(expiredEvents).toHaveLength(1);
    expect(toasts.value.map((toast) => toast.message)).toEqual([SESSION_EXPIRED_MESSAGE]);
    expect(authSession.value).toBeNull();
    expect(selectedCustomerId.value).toBeNull();
    expect(window.sessionStorage.getItem("jig-record-session")).toBeNull();
    expect(window.sessionStorage.getItem("jig-record-customer-id")).toBeNull();
    expect(window.sessionStorage.getItem(SESSION_EXPIRED_RETURN_KEY)).toBe(
      "/production/requirements?model_id=8#capacity"
    );
  });

  it("does not treat a failed unauthenticated login as an expired session", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ error: { message: "帳號或密碼錯誤" } }), {
          status: 401,
          headers: { "Content-Type": "application/json" }
        })
      )
    );
    let eventCount = 0;
    const countEvent = () => eventCount += 1;
    window.addEventListener(SESSION_EXPIRED_EVENT, countEvent);

    await expect(request("/auth/login", { method: "POST" }, false)).rejects.toMatchObject({
      status: 401,
      message: "帳號或密碼錯誤"
    });

    expect(eventCount).toBe(0);
    expect(authSession.value).toEqual(activeSession);
    expect(window.sessionStorage.getItem(SESSION_EXPIRED_RETURN_KEY)).toBeNull();
    window.removeEventListener(SESSION_EXPIRED_EVENT, countEvent);
  });
});
