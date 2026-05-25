export type StockStatus = "normal" | "low_stock" | "out_of_stock";

export interface StockSummary {
  fixture_id: number;
  fixture_code: string;
  fixture_name: string;
  stock_qty: number;
  min_stock_qty: number;
  stock_status: StockStatus;
  last_transaction_at: string | null;
}

export interface SearchResult {
  entity_type: "fixture" | "model" | "station" | "location" | "serial";
  title: string;
  subtitle: string | null;
  reference_id: number;
  stock_qty?: number | null;
  stock_status?: StockStatus | null;
  location_code?: string | null;
}

export interface MaterialTransaction {
  id: number;
  transaction_type: "receipt" | "return";
  note: string | null;
  created_at: string;
  items: Array<{
    fixture_id: number;
    fixture_code: string;
    fixture_name: string;
    qty: number;
  }>;
}

export interface FixtureImage {
  id: number;
  fixture_id: number;
  image_path: string;
  thumbnail_path: string | null;
  is_main: boolean;
}
