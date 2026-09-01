import { describe, expect, it } from "vitest";

import {
  productionMappingValidationMessage,
  productionRequirementValidationMessage
} from "@/utils/formOperations";

describe("form operation shared flows", () => {
  it("keeps production selection validation consistent across both UIs", () => {
    expect(productionMappingValidationMessage(null, null)).toBe("請輸入有效的機種代碼。");
    expect(productionMappingValidationMessage(1, null)).toBe("請輸入有效的站點代碼。");
    expect(productionMappingValidationMessage(1, 2)).toBeNull();

    expect(productionRequirementValidationMessage(null, null, 1)).toBe("請輸入有效的站點代碼。");
    expect(productionRequirementValidationMessage(2, null, 1)).toBe("請輸入有效的治具代碼。");
    expect(productionRequirementValidationMessage(2, 3, 0)).toBe("需求數量必須大於 0。");
    expect(productionRequirementValidationMessage(2, 3, 1)).toBeNull();
  });
});
