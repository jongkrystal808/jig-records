export function parseFixtureKeywords(raw: string): string[] {
  return raw
    .split(",")
    .map((part) => part.trim().toLowerCase())
    .filter(Boolean);
}

export function matchesFixtureKeywords(fixtureCode: string | null | undefined, keywords: string[]): boolean {
  if (keywords.length === 0) return true;
  const normalizedCode = (fixtureCode ?? "").trim().toLowerCase();
  return keywords.some((keyword) => normalizedCode.includes(keyword));
}
