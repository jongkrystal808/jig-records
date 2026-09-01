import { describe, expect, it } from "vitest";

import { pageAfterItemRemoval } from "./pagination";

describe("pageAfterItemRemoval", () => {
  it("returns to the previous page when removing the only item on a later page", () => {
    expect(pageAfterItemRemoval(3, 1)).toBe(2);
  });

  it("keeps the page when other rows remain or the current page is the first page", () => {
    expect(pageAfterItemRemoval(3, 2)).toBe(3);
    expect(pageAfterItemRemoval(1, 1)).toBe(1);
  });
});
