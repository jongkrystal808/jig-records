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
