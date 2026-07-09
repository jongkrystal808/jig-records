export function isStrictIdentifier(value: string): boolean {
  return /^\d+$/.test(value) && value.length <= 4;
}

export function normalizeIdentifierForWrite(value: string | null | undefined): string {
  const normalized = (value ?? "").trim();
  if (!normalized) {
    return "";
  }
  if (isStrictIdentifier(normalized)) {
    return normalized.padStart(4, "0");
  }
  return normalized;
}

export function resolveIdentifierQuery(value: string | null | undefined): { exactMatches: string[] | null; contains: string | null } {
  const token = (value ?? "").trim();
  if (!token) {
    return { exactMatches: null, contains: null };
  }
  if (isStrictIdentifier(token)) {
    const significant = token.replace(/^0+/, "") || "0";
    const exactMatches = Array.from(new Set(Array.from({ length: 5 - significant.length }, (_, index) => significant.padStart(significant.length + index, "0"))));
    return { exactMatches, contains: null };
  }
  return { exactMatches: [token], contains: null };
}
