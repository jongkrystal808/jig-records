import type { FixtureImageUploadResult } from "@/types";

import { API_ROOT, request, requestBlob } from "@/api/core";

export function fixtureImageUrlByCode(fixtureCode: string): string {
  return `${API_ROOT}/master/fixtures/${encodeURIComponent(fixtureCode)}/image`;
}

// Keep blob/image helpers isolated so the main API barrel stays focused on JSON domain clients.
export async function fetchFixtureImageObjectUrl(fixtureCode: string): Promise<string> {
  const { blob } = await requestBlob(`/master/fixtures/${encodeURIComponent(fixtureCode)}/image`, {
    headers: { Accept: "image/*, application/octet-stream;q=0.9, */*;q=0.8" }
  });
  return URL.createObjectURL(blob);
}

export const mediaApi = {
  uploadFixtureImage(fixtureId: number, customerId: number, file: File) {
    const formData = new FormData();
    formData.append("image", file);
    return request<FixtureImageUploadResult>(`/master/fixtures/${fixtureId}/image?customer_id=${encodeURIComponent(String(customerId))}`, {
      method: "POST",
      body: formData
    });
  }
};
