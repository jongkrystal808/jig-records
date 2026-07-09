import { describe, expect, it } from "vitest";

import { isStrictIdentifier, normalizeIdentifierForWrite, resolveIdentifierQuery } from "@/utils/identifier";

describe("identifier utils", () => {
  it("pads strict numeric identifiers to four digits", () => {
    expect(normalizeIdentifierForWrite("1")).toBe("0001");
    expect(normalizeIdentifierForWrite("0001")).toBe("0001");
    expect(normalizeIdentifierForWrite(" 7 ")).toBe("0007");
  });

  it("preserves legacy identifiers as-is", () => {
    expect(normalizeIdentifierForWrite("12345")).toBe("12345");
    expect(normalizeIdentifierForWrite("2024W12")).toBe("2024W12");
    expect(normalizeIdentifierForWrite(" W2401 ")).toBe("W2401");
  });

  it("returns empty string for blank input", () => {
    expect(normalizeIdentifierForWrite("")).toBe("");
    expect(normalizeIdentifierForWrite("   ")).toBe("");
  });

  it("identifies strict values using the same backend rule shape", () => {
    expect(isStrictIdentifier("1")).toBe(true);
    expect(isStrictIdentifier("1234")).toBe(true);
    expect(isStrictIdentifier("12345")).toBe(false);
    expect(isStrictIdentifier("2024W12")).toBe(false);
  });

  it("expands short numeric query input into legacy-compatible exact matches", () => {
    expect(resolveIdentifierQuery("1")).toEqual({
      exactMatches: ["1", "01", "001", "0001"],
      contains: null
    });
    expect(resolveIdentifierQuery("0001")).toEqual({
      exactMatches: ["1", "01", "001", "0001"],
      contains: null
    });
    expect(resolveIdentifierQuery("0")).toEqual({
      exactMatches: ["0", "00", "000", "0000"],
      contains: null
    });
  });

  it("uses exact raw match for legacy query input", () => {
    expect(resolveIdentifierQuery("12345")).toEqual({
      exactMatches: ["12345"],
      contains: null
    });
    expect(resolveIdentifierQuery(" 2024W12 ")).toEqual({
      exactMatches: ["2024W12"],
      contains: null
    });
    expect(resolveIdentifierQuery("")).toEqual({
      exactMatches: null,
      contains: null
    });
  });
});
