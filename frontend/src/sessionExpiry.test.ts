// @vitest-environment jsdom

import { afterEach, describe, expect, it } from "vitest";

import {
  clearSessionExpiredReturnPath,
  consumeSessionExpiredReturnPath,
  rememberSessionExpiredReturnPath,
  SESSION_EXPIRED_RETURN_KEY
} from "@/sessionExpiry";

afterEach(() => {
  window.sessionStorage.clear();
  window.history.replaceState({}, "", "/");
});

describe("session expiry return path", () => {
  it("preserves route query and hash until login succeeds", () => {
    window.history.replaceState({}, "", "/master/quality?issue=missing_image#row-7");

    expect(rememberSessionExpiredReturnPath()).toBe(
      "/master/quality?issue=missing_image#row-7"
    );
    expect(consumeSessionExpiredReturnPath()).toBe(
      "/master/quality?issue=missing_image#row-7"
    );
    expect(window.sessionStorage.getItem(SESSION_EXPIRED_RETURN_KEY)).toBeNull();
  });

  it("does not save the login page and clears stale paths on demand", () => {
    window.sessionStorage.setItem(SESSION_EXPIRED_RETURN_KEY, "/inventory");
    clearSessionExpiredReturnPath();
    window.history.replaceState({}, "", "/login?reason=expired");

    expect(rememberSessionExpiredReturnPath()).toBeNull();
    expect(window.sessionStorage.getItem(SESSION_EXPIRED_RETURN_KEY)).toBeNull();
  });
});
