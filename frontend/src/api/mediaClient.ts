import { API_ROOT } from "@/api/core";
import { extractErrorMessage } from "@/utils/apiError";

export function fixtureImageUrlByCode(fixtureCode: string): string {
  return `${API_ROOT}/master/fixtures/${encodeURIComponent(fixtureCode)}/image`;
}

// Keep blob/image helpers isolated so the main API barrel stays focused on JSON domain clients.
export async function fetchFixtureImageObjectUrl(fixtureCode: string): Promise<string> {
  const response = await fetch(fixtureImageUrlByCode(fixtureCode), {
    headers: { Accept: "image/*, application/octet-stream;q=0.9, */*;q=0.8" }
  });
  if (!response.ok) {
    throw new Error(extractErrorMessage(await response.text(), `Request failed: ${response.status}`));
  }
  const blob = await response.blob();
  return URL.createObjectURL(blob);
}
