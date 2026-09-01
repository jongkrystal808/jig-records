<script setup lang="ts">
import UiMultiSelect from "@/components/common/UiMultiSelect.vue";
import type {
  ConfigurationReportOption,
  ModelQueryStationRequirement,
  StationCapacity
} from "@/types";
import type { ReportTransactionMode } from "@/utils/reportTransactionFilters";

type WaterStatus = "normal" | "low" | "empty" | "na";
type WaterFilter = "attention" | "low" | "empty" | "normal";
type FixtureStatusFilter = "active" | "inactive";
type ReportFilters = {
  keyword: string;
  fixtureStatus: FixtureStatusFilter[];
  fixtureId: string;
  stationId: string;
  modelId: string;
  waterStatus: WaterFilter[];
  storage: string;
  configurationStatus: Array<"configured" | "unconfigured" | "unbound">;
};
type TransactionActivityFilters = {
  mode: ReportTransactionMode;
  dateFrom: string;
  dateTo: string;
  ownershipType: Array<"customer_supplied" | "self_purchased">;
};
type FilterChip = { key: string; label: string; value: string };
type LinkedFilterKey = Exclude<keyof ReportFilters, "fixtureStatus">;

const props = defineProps<{
  collapsed: boolean;
  draftFilters: ReportFilters;
  transactionFilters: TransactionActivityFilters;
  orderedFilterChips: FilterChip[];
  fixtures: ConfigurationReportOption[];
  models: ConfigurationReportOption[];
  stations: ConfigurationReportOption[];
  availableWaterStatuses: Set<WaterStatus>;
  activeFilterCount: number;
  pendingFilterCount: number;
  reportTotal: number;
  loading: boolean;
  transactionFilterLoading: boolean;
  canRunSearch: boolean;
  canCalculateCapacity: boolean;
  capacityLoading: boolean;
  capacityResults: StationCapacity[];
  capacityRequirementsByStationId: Map<number, ModelQueryStationRequirement[]>;
  expandedBottleneckStationIds: Set<number>;
  hasAppliedStation: boolean;
  transactionDateValidationMessage: string;
  usesTransactionDateRange: boolean;
}>();

const emit = defineEmits<{
  "update:collapsed": [value: boolean];
  clear: [];
  removeFilter: [key: string];
  filterChange: [key: LinkedFilterKey];
  fixtureStatusChange: [];
  transactionModeChange: [];
  runSearch: [];
  calculateCapacity: [];
  closeCapacity: [];
  toggleBottleneck: [stationId: number];
}>();

function waterOptionAvailable(value: WaterFilter): boolean {
  if (value === "attention") {
    return props.availableWaterStatuses.has("low") || props.availableWaterStatuses.has("empty");
  }
  return props.availableWaterStatuses.has(value);
}

function capacityRequirements(stationId: number): ModelQueryStationRequirement[] {
  return props.capacityRequirementsByStationId.get(stationId) ?? [];
}

function stockStatusLabel(status: ModelQueryStationRequirement["stock_status"]): string {
  if (status === "out_of_stock") return "缺料";
  if (status === "low_stock") return "低水位";
  return "正常";
}
</script>

<template>
  <section
    class="filter-panel"
    :class="{ collapsed }"
    data-tour="report-filter-panel"
    aria-label="報表篩選條件"
  >
    <div class="filter-panel-title">
      <div>
        <strong>篩選條件</strong>
        <span>依選擇順序聯動，第一個條件優先</span>
      </div>
      <div class="filter-panel-title-actions">
        <button
          class="mobile-filter-toggle"
          type="button"
          :aria-expanded="!collapsed"
          @click="emit('update:collapsed', !collapsed)"
        >
          {{ collapsed ? "更多條件" : "收合條件" }}
        </button>
        <button
          v-if="activeFilterCount || pendingFilterCount"
          class="text-button"
          type="button"
          @click="emit('clear')"
        >
          清除全部
        </button>
      </div>
    </div>

    <div
      v-if="orderedFilterChips.length"
      class="filter-priority-chips"
      data-tour="report-filter-priority"
      aria-label="聯動篩選順序"
    >
      <span>聯動順序</span>
      <button
        v-for="(chip, index) in orderedFilterChips"
        :key="chip.key"
        type="button"
        :aria-label="`移除第 ${index + 1} 順位的${chip.label}條件`"
        @click="emit('removeFilter', chip.key)"
      >
        <i>{{ index + 1 }}</i>
        <b>{{ chip.label }}</b>
        <em>{{ chip.value }}</em>
        <strong aria-hidden="true">×</strong>
      </button>
    </div>

    <div v-if="collapsed" class="mobile-filter-summary">
      <label class="mobile-keyword-filter">
        <span>關鍵字</span>
        <input
          v-model="draftFilters.keyword"
          type="search"
          aria-label="報表關鍵字"
          placeholder="治具、機種、站點或名稱"
          @input="emit('filterChange', 'keyword')"
          @keydown.enter.prevent="emit('runSearch')"
        />
      </label>
      <div class="mobile-filter-result">
        <span>已套用 {{ activeFilterCount }} 個條件</span>
        <strong>{{ reportTotal.toLocaleString("zh-TW") }} 筆結果</strong>
        <em v-if="pendingFilterCount">有 {{ pendingFilterCount }} 個條件尚未套用</em>
      </div>
      <div class="mobile-filter-summary-actions">
        <button type="button" @click="emit('update:collapsed', false)">更多條件</button>
        <button
          class="mobile-summary-query"
          type="button"
          :disabled="!canRunSearch"
          @click="emit('runSearch')"
        >
          {{ transactionFilterLoading ? "套用中…" : "套用條件" }}
        </button>
      </div>
    </div>

    <div class="filter-grid" data-tour="report-filter-fields">
      <label class="keyword-field">
        <span>關鍵字</span>
        <input
          v-model="draftFilters.keyword"
          type="search"
          placeholder="治具、機種、站點或名稱"
          @input="emit('filterChange', 'keyword')"
          @keydown.enter.prevent="emit('runSearch')"
        />
      </label>

      <label>
        <span>治具</span>
        <select v-model="draftFilters.fixtureId" aria-label="治具篩選" @change="emit('filterChange', 'fixtureId')">
          <option value="">全部治具</option>
          <option v-for="fixture in fixtures" :key="fixture.id" :value="String(fixture.id)">
            {{ fixture.code }}－{{ fixture.name }}
          </option>
        </select>
      </label>

      <UiMultiSelect v-model="draftFilters.fixtureStatus" label="治具狀態" placeholder="所有治具" :options="[{ value: 'active', label: '已啟用' }, { value: 'inactive', label: '已停用' }]" @change="emit('fixtureStatusChange')" />

      <label>
        <span>機種</span>
        <select v-model="draftFilters.modelId" aria-label="機種篩選" @change="emit('filterChange', 'modelId')">
          <option value="">全部機種</option>
          <option v-for="model in models" :key="model.id" :value="String(model.id)">{{ model.code }}</option>
        </select>
      </label>

      <label>
        <span>站點</span>
        <select v-model="draftFilters.stationId" aria-label="站點篩選" @change="emit('filterChange', 'stationId')">
          <option value="">全部站點</option>
          <option v-for="station in stations" :key="station.id" :value="String(station.id)">
            {{ station.code }}－{{ station.name }}
          </option>
        </select>
      </label>

      <UiMultiSelect
        v-model="draftFilters.waterStatus"
        label="水位狀態"
        placeholder="全部水位"
        :options="[
          { value: 'low', label: '低水位', disabled: !waterOptionAvailable('low') },
          { value: 'empty', label: '缺料', disabled: !waterOptionAvailable('empty') },
          { value: 'normal', label: '正常', disabled: !waterOptionAvailable('normal') }
        ]"
        @change="emit('filterChange', 'waterStatus')"
      />

      <label>
        <span>儲位</span>
        <input
          v-model="draftFilters.storage"
          type="search"
          placeholder="產線或部門儲位"
          @input="emit('filterChange', 'storage')"
          @keydown.enter.prevent="emit('runSearch')"
        />
      </label>

      <label>
        <span>收退料</span>
        <select v-model="transactionFilters.mode" @change="emit('transactionModeChange')">
          <option value="">不篩選收退料</option>
          <option value="today_receipt">今日收料</option>
          <option value="today_return">今日退料</option>
          <option value="range_receipt">指定日期收料</option>
          <option value="range_return">指定日期退料</option>
        </select>
      </label>

      <UiMultiSelect v-model="transactionFilters.ownershipType" label="交易來源" placeholder="全部來源" :disabled="!transactionFilters.mode" :options="[{ value: 'customer_supplied', label: '客供' }, { value: 'self_purchased', label: '自購' }]" />

      <label class="date-field">
        <span>起始日期</span>
        <input
          v-model="transactionFilters.dateFrom"
          type="date"
          :disabled="!usesTransactionDateRange"
          :aria-invalid="Boolean(transactionDateValidationMessage)"
          :aria-describedby="transactionDateValidationMessage ? 'transaction-date-hint transaction-date-error' : 'transaction-date-hint'"
        />
      </label>

      <label class="date-field">
        <span>結束日期</span>
        <input
          v-model="transactionFilters.dateTo"
          type="date"
          :disabled="!usesTransactionDateRange"
          :aria-invalid="Boolean(transactionDateValidationMessage)"
          :aria-describedby="transactionDateValidationMessage ? 'transaction-date-hint transaction-date-error' : 'transaction-date-hint'"
        />
        <small v-if="transactionDateValidationMessage" id="transaction-date-error" class="field-error" role="alert">
          {{ transactionDateValidationMessage }}
        </small>
      </label>

      <div class="filter-actions" data-tour="report-filter-actions">
        <button class="secondary-button" type="button" @click="emit('clear')">重設</button>
        <button
          class="capacity-button"
          data-tour="report-capacity-trigger"
          type="button"
          :disabled="!canCalculateCapacity || capacityLoading"
          @click="emit('calculateCapacity')"
        >
          {{ capacityLoading ? "計算中…" : "計算最大開站數" }}
        </button>
        <button class="primary-button" type="button" :disabled="!canRunSearch" @click="emit('runSearch')">
          {{ transactionFilterLoading ? "套用中…" : "套用條件" }}
        </button>
      </div>

      <p id="transaction-date-hint" class="transaction-date-hint">
        日期只會套用在「指定日期收料／退料」；未選收退料模式時不參與其他條件篩選。
      </p>

      <div v-if="capacityResults.length" class="capacity-result" role="status">
        <header>
          <div>
            <span>{{ hasAppliedStation ? "指定站點計算結果" : "全部站點計算結果" }}</span>
            <strong>{{ capacityResults[0].model_code }}</strong>
            <small>共 {{ capacityResults.length }} 個站點</small>
          </div>
          <button type="button" aria-label="關閉最大開站數結果" @click="emit('closeCapacity')">關閉</button>
        </header>
        <div class="capacity-result-list">
          <article
            v-for="capacity in capacityResults"
            :key="capacity.station_id"
            :class="{ expanded: expandedBottleneckStationIds.has(capacity.station_id) }"
          >
            <div>
              <strong>{{ capacity.station_code }}</strong>
              <span>{{ capacity.station_name || "—" }}</span>
            </div>
            <dl><div><dt>最大開站數</dt><dd>{{ capacity.max_open_station_count }} 站</dd></div></dl>
            <button
              class="capacity-bottleneck-toggle"
              type="button"
              :aria-expanded="expandedBottleneckStationIds.has(capacity.station_id)"
              @click="emit('toggleBottleneck', capacity.station_id)"
            >
              {{ expandedBottleneckStationIds.has(capacity.station_id) ? "收起治具明細" : "查看治具明細" }}
            </button>
            <div v-if="expandedBottleneckStationIds.has(capacity.station_id)" class="capacity-detail-table-wrap">
              <table class="capacity-detail-table">
                <thead><tr><th>治具代碼</th><th>治具名稱</th><th>需求數量</th><th>目前庫存</th><th>此治具可支援站數</th><th>狀態</th></tr></thead>
                <tbody>
                  <tr
                    v-for="requirement in capacityRequirements(capacity.station_id)"
                    :key="`${capacity.station_id}-${requirement.fixture_id}`"
                    :class="{ bottleneck: requirement.fixture_code === capacity.bottleneck_fixture_code }"
                  >
                    <td>
                      <strong>{{ requirement.fixture_code }}</strong>
                      <small v-if="requirement.fixture_code === capacity.bottleneck_fixture_code">瓶頸</small>
                    </td>
                    <td>{{ requirement.fixture_name || "—" }}</td>
                    <td>{{ requirement.required_qty }}</td>
                    <td>{{ requirement.stock_qty }}</td>
                    <td>{{ requirement.max_open_station_count }}</td>
                    <td><span :class="`capacity-stock-status ${requirement.stock_status}`">{{ stockStatusLabel(requirement.stock_status) }}</span></td>
                  </tr>
                  <tr v-if="capacityRequirements(capacity.station_id).length === 0">
                    <td colspan="6" class="capacity-detail-empty">此站點尚未配置治具需求</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </article>
        </div>
      </div>
    </div>
  </section>
</template>
