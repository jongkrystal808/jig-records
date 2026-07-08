export type StockStatus = "normal" | "low_stock" | "out_of_stock";

export function fallbackText(value: string | null | undefined, fallback = "-"): string {
  return value && value.trim() ? value : fallback;
}

export function stockStatusLabel(status: StockStatus): string {
  if (status === "low_stock") return "低水位";
  if (status === "out_of_stock") return "缺料";
  return "正常";
}

export function ownershipLabel(type: "customer_supplied" | "self_purchased"): string {
  return type === "customer_supplied" ? "客供" : "自購";
}

export function capacityStateLabel(state: "idle" | "good" | "warn" | "danger"): string {
  if (state === "danger") return "滿載";
  if (state === "warn") return "接近上限";
  if (state === "idle") return "未設定";
  return "正常";
}

type IdentifierStockEntry = [identifier: string, quantity: number];

type IdentifierRangeGroup = {
  start: string;
  end: string;
  quantity: number;
  startValue: number;
  endValue: number;
  width: number;
};

function parseNumericIdentifier(identifier: string): { value: number; width: number } | null {
  if (!/^\d+$/.test(identifier)) {
    return null;
  }
  return {
    value: Number(identifier),
    width: identifier.length
  };
}

function flushIdentifierRange(group: IdentifierRangeGroup, formatCount: (value: number) => string): string {
  const label = group.startValue === group.endValue ? group.start : `${group.start}-${group.end}`;
  return `${label}（${formatCount(group.quantity)}）`;
}

export function formatIdentifierStockTags(
  entries: Iterable<IdentifierStockEntry>,
  formatCount: (value: number) => string
): string[] {
  const rows = [...entries].slice().sort((a, b) => a[0].localeCompare(b[0], "zh-TW", { numeric: true }));
  const tags: string[] = [];
  let pendingRange: IdentifierRangeGroup | null = null;

  for (const [identifier, quantity] of rows) {
    const parsed = parseNumericIdentifier(identifier);
    if (!parsed) {
      if (pendingRange) {
        tags.push(flushIdentifierRange(pendingRange, formatCount));
        pendingRange = null;
      }
      tags.push(`${identifier}（${formatCount(quantity)}）`);
      continue;
    }

    if (
      pendingRange &&
      pendingRange.quantity === quantity &&
      pendingRange.width === parsed.width &&
      parsed.value === pendingRange.endValue + 1
    ) {
      pendingRange.end = identifier;
      pendingRange.endValue = parsed.value;
      continue;
    }

    if (pendingRange) {
      tags.push(flushIdentifierRange(pendingRange, formatCount));
    }

    pendingRange = {
      start: identifier,
      end: identifier,
      quantity,
      startValue: parsed.value,
      endValue: parsed.value,
      width: parsed.width
    };
  }

  if (pendingRange) {
    tags.push(flushIdentifierRange(pendingRange, formatCount));
  }

  return tags;
}
