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
  has_image: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface PageResult<T> {
  items: T[];
  page: number;
  page_size: number;
  total: number;
}

export interface FixtureImageUploadResult {
  fixture_id: number;
  fixture_code: string;
  has_image: boolean;
  fixture: Fixture;
}

export interface FixtureImageBatchUploadItem {
  file_name: string;
  fixture_code: string | null;
  fixture_id: number | null;
  success: boolean;
  message: string;
}

export interface FixtureImageBatchUploadResult {
  requested_count: number;
  uploaded_count: number;
  failed_count: number;
  results: FixtureImageBatchUploadItem[];
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

export interface MachineModelDeleteResult {
  model_id: number;
  model_code: string;
  deleted_model_station_count: number;
  deleted_requirement_count: number;
  deleted_capacity_summary_count: number;
}

export interface Station {
  id: number;
  customer_id: number;
  code: string;
  name: string;
  is_active: boolean;
}

export interface StationDeleteResult {
  station_id: number;
  station_code: string;
  deleted_model_station_count: number;
  deleted_requirement_count: number;
  deleted_capacity_summary_count: number;
}

export interface AppUser {
  id: number;
  username: string;
  email: string | null;
  display_name: string;
  role: string;
  is_active: boolean;
  allowed_customer_ids: number[];
  allowed_customers?: Array<{ id: number; code: string; name: string }>;
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

export interface StorageContainer {
  id: number;
  customer_id: number;
  name: string;
  description: string | null;
  code_count: number;
  fixture_type_count: number;
  total_quantity: number;
  pending_quantity_count: number;
  created_at?: string;
  updated_at?: string;
}

export interface StorageCode {
  id: number;
  customer_id: number;
  container_id: number | null;
  container_name: string | null;
  code: string;
  is_active: boolean;
  fixture_type_count: number;
  total_quantity: number;
  pending_quantity_count: number;
  created_at?: string;
  updated_at?: string;
}

export interface StorageOverview {
  customer_id: number;
  containers: StorageContainer[];
  codes: StorageCode[];
  ungrouped_code_count: number;
  pending_quantity_count: number;
}

export interface StorageStationOption {
  model_id: number;
  model_code: string;
  model_name: string;
  station_id: number;
  station_code: string;
  station_name: string;
}

export interface FixturePlacement {
  id: number;
  fixture_id: number;
  target_type: "storage_code" | "model_station";
  storage_code_id: number | null;
  storage_code: string | null;
  container_id: number | null;
  container_name: string | null;
  model_id: number | null;
  model_code: string | null;
  model_name: string | null;
  station_id: number | null;
  station_code: string | null;
  station_name: string | null;
  quantity: number | null;
  source: string;
  display_label: string;
  created_at?: string;
  updated_at?: string;
}

export interface FixturePlacementDetail {
  fixture_id: number;
  fixture_code: string;
  fixture_name: string;
  customer_id: number;
  stock_qty: number;
  allocated_qty: number;
  unallocated_qty: number;
  has_pending_quantities: boolean;
  placements: FixturePlacement[];
  station_options: StorageStationOption[];
}

export interface FixturePlacementInput {
  target_type: "storage_code" | "model_station";
  storage_code_id?: number | null;
  model_id?: number | null;
  station_id?: number | null;
  quantity: number | null;
}

export interface ModelShortcutPreference {
  model_id: number;
  model_code: string;
  query_count: number;
  last_queried_at: string | null;
  pinned: boolean;
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
  customer_supplied_qty: number;
  self_purchased_qty: number;
  min_stock_qty: number;
  stock_status: StockStatus;
  last_transaction_at: string | null;
}

export interface IdentifierStockSummary {
  fixture_id: number;
  identifier: string;
  stock_qty: number;
  customer_supplied_qty: number;
  self_purchased_qty: number;
}

export interface DashboardRecentTransactionEntry {
  transaction_id: number;
  transaction_item_id: number;
  transaction_no: string | null;
  occurred_at: string;
  fixture_code: string;
  identifier: string | null;
  quantity: number;
}

export interface InventoryDashboardSummary {
  today_receipt_qty: number;
  today_return_qty: number;
  low_stock_count: number;
  low_stock_preview_entries: Array<{
    fixture_id: number;
    fixture_code: string;
    fixture_name: string;
    stock_qty: number;
    customer_supplied_qty: number;
    self_purchased_qty: number;
    min_stock_qty: number;
    stock_status: "low_stock" | "out_of_stock";
  }>;
  has_more_low_stock_entries: boolean;
  recent_receipt_entries: DashboardRecentTransactionEntry[];
  recent_return_entries: DashboardRecentTransactionEntry[];
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
  matched_identifier?: string | null;
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
  transaction_no: string | null;
  occurred_at: string;
  actor_user_id: number | null;
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

export interface MaterialTransactionPage {
  items: MaterialTransaction[];
  page: number;
  page_size: number;
  total: number;
}

export interface TransactionOverviewRow {
  id: number;
  transaction_type: "receipt" | "return";
  transaction_no: string | null;
  occurred_at: string;
  actor_user_id: number | null;
  created_by: string;
  fixture_id: number | null;
  fixture_code: string;
  fixture_name: string;
  ownership_type: "customer_supplied" | "self_purchased";
  identifier: string | null;
  quantity: number;
  note: string | null;
}

export interface TransactionOverviewPage {
  items: TransactionOverviewRow[];
  page: number;
  page_size: number;
  total: number;
}

export interface ConfigurationReportRow {
  key: string;
  customer_code: string;
  fixture_id: number;
  fixture_code: string;
  fixture_name: string;
  stock_qty: number | null;
  customer_supplied_qty: number | null;
  self_purchased_qty: number | null;
  min_stock_qty: number | null;
  water_status: "normal" | "low" | "empty" | "na";
  line_storage: string;
  department_storage: string;
  model_id: number;
  model_code: string;
  station_id: number;
  station_code: string;
  station_name: string;
  required_qty: number | null;
  max_open_station_count: number | null;
  configuration_status: "configured" | "unconfigured" | "unbound";
}

export interface ConfigurationReportPage {
  items: ConfigurationReportRow[];
  page: number;
  page_size: number;
  total: number;
  fixture_count: number;
  attention_fixture_count: number;
  missing_configuration_count: number;
  total_stock_qty: number;
  customer_supplied_qty: number;
  self_purchased_qty: number;
  populated_columns: string[];
  transaction_details: TransactionOverviewRow[];
  transaction_detail_count: number;
}

export interface ConfigurationReportOption {
  id: number;
  code: string;
  name: string;
}

export interface ConfigurationReportOptions {
  fixtures: ConfigurationReportOption[];
  models: ConfigurationReportOption[];
  stations: ConfigurationReportOption[];
  water_statuses: Array<"normal" | "low" | "empty">;
}

export interface ConfigurationReportQuery {
  customer_id: number;
  page?: number;
  page_size?: number;
  keyword?: string;
  fixture_status?: Array<"active" | "inactive">;
  fixture_id?: number;
  model_id?: number;
  station_id?: number;
  water_status?: Array<"attention" | "low" | "empty" | "normal">;
  storage?: string;
  configuration_status?: Array<"configured" | "unconfigured" | "unbound">;
  transaction_type?: Array<"receipt" | "return">;
  ownership_type?: Array<"customer_supplied" | "self_purchased">;
  date_from?: string;
  date_to?: string;
  sort_by?: string;
  sort_direction?: "asc" | "desc";
  priority?: string;
  include_transaction_details?: boolean;
}

export interface TransactionReverseResult {
  transaction_id: number;
  transaction_no: string | null;
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
  transaction_type?: "receipt" | "return" | Array<"receipt" | "return">;
  ownership_type?: "customer_supplied" | "self_purchased" | Array<"customer_supplied" | "self_purchased">;
  date_from?: string;
  date_to?: string;
  fixture_code?: string;
  transaction_no?: string;
  identifier?: string;
  created_by?: string;
}

export interface StockTransactionCreate {
  customer_id: number;
  occurred_at?: string;
  transaction_no: string;
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

export interface ModelStationListItem extends ModelStation {
  model_code: string;
  model_name: string;
  station_code: string;
  station_name: string;
}

export interface FixtureRequirement {
  id: number;
  model_id: number;
  station_id: number;
  fixture_id: number;
  required_qty: number;
  designated_mode?: boolean;
  designated_identifiers?: string[];
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
  designated_mode?: boolean;
  designated_identifiers?: string[];
  stock_qty?: number;
}

export interface FixtureRequirementCopyResult {
  source_requirement_count: number;
  created_count: number;
  updated_count: number;
  skipped_count: number;
  mapping_created: boolean;
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
  designated_mode: boolean;
  designated_identifiers: string[];
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
