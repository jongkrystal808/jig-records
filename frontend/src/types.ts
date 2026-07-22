export type StockStatus = "normal" | "low_stock" | "out_of_stock";

export interface Customer {
  id: number;
  code: string;
  name: string;
  assigned_user_ids: number[];
  created_at?: string;
  updated_at?: string;
}

export interface Fixture {
  id: number;
  customer_id: number;
  responsible_user_id: number | null;
  code: string;
  name: string;
  line_storage_location: string | null;
  department_storage_location: string | null;
  min_stock_qty: number;
  description: string | null;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface FixtureQualityRow {
  fixture_id: number;
  fixture_code: string;
  fixture_name: string | null;
  storage_location: string | null;
  min_stock_qty: number;
  stock_qty: number;
  identifier_stock_qty: number;
  related_model_count: number;
  has_image: boolean;
  issue_codes: string[];
}

export interface FixtureQualityReport {
  total_fixture_count: number;
  problematic_fixture_count: number;
  missing_name_count: number;
  missing_storage_location_count: number;
  missing_image_count: number;
  missing_min_stock_qty_count: number;
  missing_model_relation_count: number;
  stock_mismatch_count: number;
  rows: FixtureQualityRow[];
}

export interface MachineModel {
  id: number;
  customer_id: number;
  code: string;
  name: string;
  is_active: boolean;
}

export interface Station {
  id: number;
  customer_id: number;
  code: string;
  name: string;
  is_active: boolean;
}

export interface AppUser {
  id: number;
  username: string;
  email: string | null;
  display_name: string;
  role: string;
  is_active: boolean;
  allowed_customer_ids: number[];
  created_at: string;
  updated_at: string;
}

export interface AuthSession {
  mode: "user" | "guest";
  user: AppUser | null;
  display_name: string;
  token: string;
  role: string;
}

export interface AuditLogEntry {
  id: number;
  customer_id: number | null;
  entity_type: string;
  entity_key: string;
  action: string;
  summary: string;
  actor_user_id: number | null;
  actor_username: string;
  actor_display_name: string;
  actor_role: string;
  created_at: string;
  updated_at: string;
}

export interface StockSummary {
  fixture_id: number;
  fixture_code: string;
  fixture_name: string;
  stock_qty: number;
  min_stock_qty: number;
  stock_status: StockStatus;
  last_transaction_at: string | null;
}

export interface IdentifierStockSummary {
  fixture_id: number;
  identifier: string;
  stock_qty: number;
}

export interface SearchResult {
  entity_type: "fixture" | "model" | "station";
  title: string;
  subtitle: string | null;
  reference_id: number;
  is_active: boolean;
  stock_qty?: number | null;
  stock_status?: StockStatus | null;
  location_code?: string | null;
}

export interface SearchResultPage {
  items: SearchResult[];
  page: number;
  page_size: number;
  total: number;
  has_more: boolean;
}

export interface SearchFixtureStationRow {
  model_id: number;
  model_code: string;
  model_name: string;
  station_id: number;
  station_code: string;
  station_name: string;
  required_qty: number;
}

export interface SearchFixtureContext {
  fixture: Fixture;
  stock: StockSummary | null;
  identifier_rows: IdentifierStockSummary[];
  related_models: MachineModel[];
  station_rows: SearchFixtureStationRow[];
  transactions: MaterialTransaction[];
}

export interface SearchModelContext {
  model: MachineModel;
  query: ModelQuery;
}

export interface MaterialTransaction {
  id: number;
  customer_id: number;
  transaction_type: "receipt" | "return";
  transaction_no: string;
  occurred_at: string;
  created_by: string;
  note: string | null;
  created_at: string;
  items: Array<{
    fixture_id: number | null;
    fixture_code: string;
    fixture_name: string;
    ownership_type: "customer_supplied" | "self_purchased";
    identifier: string | null;
    quantity: number;
    note: string | null;
  }>;
}

export interface TransactionReverseResult {
  transaction_id: number;
  transaction_no: string;
  transaction_type: "receipt" | "return";
  item_count: number;
  total_quantity: number;
}

export interface InventoryRecalculateResult {
  customer_id: number | null;
  fixture_count: number;
  transaction_count: number;
  item_count: number;
}

export interface TransactionQueryFilters {
  transaction_type?: "receipt" | "return";
  date_from?: string;
  date_to?: string;
  fixture_code?: string;
  transaction_no?: string;
  identifier?: string;
  created_by?: string;
}

export interface StockTransactionCreate {
  customer_id: number;
  created_by: string;
  occurred_at?: string;
  transaction_no?: string;
  note?: string;
  items: Array<{
    fixture_id: number;
    ownership_type: "customer_supplied" | "self_purchased";
    identifier: string;
    quantity: number;
    note?: string;
  }>;
}

export interface ModelStation {
  id: number;
  model_id: number;
  station_id: number;
}

export interface FixtureRequirement {
  id: number;
  model_id: number;
  station_id: number;
  fixture_id: number;
  required_qty: number;
}

export interface FixtureRequirementListItem {
  id: number;
  model_id: number;
  model_code: string;
  station_id: number;
  station_code: string;
  fixture_id: number;
  fixture_code: string;
  fixture_name: string;
  required_qty: number;
}

export interface StationCapacity {
  model_id: number;
  model_code: string;
  station_id: number;
  station_code: string;
  station_name: string;
  max_open_station_count: number;
  bottleneck_fixture_code: string | null;
}

export interface ModelQueryFixture {
  fixture_id: number;
  fixture_code: string;
  fixture_name: string;
  stock_qty: number;
  min_stock_qty: number;
  required_per_station: number;
  max_open_station_count: number;
  stock_status: StockStatus;
}

export interface ModelQueryStation {
  station_id: number;
  station_code: string;
  station_name: string;
  max_open_station_count: number;
  bottleneck_fixture_code: string | null;
}

export interface ModelQueryStationRequirement {
  station_id: number;
  station_code: string;
  fixture_id: number;
  fixture_code: string;
  fixture_name: string;
  required_qty: number;
  stock_qty: number;
  max_open_station_count: number;
  stock_status: StockStatus;
}

export interface ModelQuery {
  model_id: number;
  model_code: string;
  model_name: string;
  max_open_station_count: number;
  station_count: number;
  fixture_type_count: number;
  total_stock_qty: number;
  stations: ModelQueryStation[];
  station_requirements: ModelQueryStationRequirement[];
  fixtures: ModelQueryFixture[];
}
