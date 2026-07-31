export type TourPlacement = "top" | "bottom" | "left" | "right";

export type OnboardingFlowId =
  | "guest-search-report"
  | "search-basics"
  | "inventory-workflow"
  | "master-basics"
  | "production-workflow"
  | "system-detailed-guide"
  | "admin-inventory-governance";

export interface OnboardingStepNote {
  /** "warning" 用在不可逆或需要特別小心的操作；"info" 用在一般補充說明 */
  tone: "warning" | "info";
  text: string;
}

export interface OnboardingStepExample {
  /** 這個範例對應的情境標籤，例如「兩行格式」「TAB 格式」 */
  label?: string;
  value: string;
}

export interface OnboardingStepImage {
  /** 對應 public/ 底下的路徑或完整網址 */
  src: string;
  alt: string;
}

export interface OnboardingStep {
  id: string;
  route: string;
  query?: Record<string, string>;
  target: string;
  title: string;
  description: string;
  /** 條列式子步驟或重點，會顯示在 description 下方 */
  bullets?: string[];
  /** 一個或多個範例值，會以等寬字體卡片呈現 */
  example?: OnboardingStepExample[];
  /** 需要特別提醒的注意事項，會以醒目提示框呈現 */
  note?: OnboardingStepNote;
  /** 搭配截圖或示意圖，幫助理解畫面位置 */
  image?: OnboardingStepImage;
  placement?: TourPlacement;
  openBatchModal?: boolean;
  openMoreMenu?: boolean;
  openExportModal?: boolean;
  sandboxMode?: boolean;
}

export interface OnboardingFlow {
  id: OnboardingFlowId;
  sectionLabel: string;
  label: string;
  summary: string;
  requiresInventoryAccess?: boolean;
  requiresMasterAccess?: boolean;
  requiresAdminAccess?: boolean;
  guestOnly?: boolean;
  steps: OnboardingStep[];
}

export const onboardingFlows: OnboardingFlow[] = [
  {
    id: "guest-search-report",
    sectionLabel: "訪客首頁",
    label: "查詢工作台與庫存配置報表",
    summary: "一次認識訪客可使用的查詢與報表功能。",
    guestOnly: true,
    steps: [
      {
        id: "guest-home-mode-switch",
        route: "/search",
        query: { home_mode: "query" },
        target: "[data-tour='home-mode-switch']",
        title: "首頁可在查詢與報表間切換",
        description: "訪客登入後預設開啟報表；需要查單一治具或機種時，可直接切到查詢工作台。",
        placement: "bottom"
      },
      {
        id: "guest-search-mode",
        route: "/search",
        query: { home_mode: "query" },
        target: "[data-tour='search-mode-switch']",
        title: "先選治具或機種",
        description: "治具模式適合查看庫存、圖片與關聯資料；機種模式適合查看站點與所需治具。",
        placement: "bottom"
      },
      {
        id: "guest-search-input",
        route: "/search",
        query: { home_mode: "query" },
        target: "[data-tour='search-query-field']",
        title: "輸入代碼或名稱開始查詢",
        description: "可輸入治具代碼、治具名稱或機種代碼，選取結果後查看詳細內容。",
        placement: "bottom"
      },
      {
        id: "guest-report-switch",
        route: "/search",
        query: { home_mode: "report" },
        target: "[data-tour='home-mode-switch']",
        title: "切到報表查看整體庫存與配置",
        description: "報表模式會組合治具、庫存、機種與站點，適合一次檢查多筆資料。",
        placement: "bottom"
      },
      {
        id: "guest-report-filters",
        route: "/search",
        query: { home_mode: "report" },
        target: "[data-tour='report-filter-panel']",
        title: "用聯動條件縮小報表範圍",
        description: "可依治具、機種、站點、水位、儲位與今日／指定日期收退料篩選；日期只有搭配收料或退料模式才會生效。",
        placement: "bottom"
      },
      {
        id: "guest-report-capacity",
        route: "/search",
        query: { home_mode: "report" },
        target: "[data-tour='report-capacity-trigger']",
        title: "選好機種後計算各站點最大開站數",
        description: "只選機種並保留「全部站點」會列出所有已綁定站點；再指定站點則只計算該站。瓶頸治具預設收起，需要時可逐站展開。",
        placement: "bottom"
      },
      {
        id: "guest-report-results",
        route: "/search",
        query: { home_mode: "report" },
        target: "[data-tour='report-result-table']",
        title: "報表支援圖片、欄位選擇與篩選結果匯出",
        description: "點治具代碼可看圖片；右上可選顯示欄位，匯出時會輸出全部符合篩選的資料。",
        placement: "top"
      }
    ]
  },
  {
    id: "search-basics",
    sectionLabel: "首頁查詢",
    label: "查詢工作台",
    summary: "從首頁查詢、切換區塊，到重播教學入口的基本操作。",
    steps: [
      {
        id: "search-onboarding-entry",
        route: "/search/detail",
        target: "[data-tour='search-onboarding-entry']",
        title: "右下角固定保留教學入口",
        description: "點這裡開啟教學選單，之後想重看其他教學也從這裡進。",
        placement: "bottom"
      },
      {
        id: "search-mode",
        route: "/search/detail",
        target: "[data-tour='search-mode-switch']",
        title: "先決定查治具還是查機種",
        description: "兩種模式對應不同的資料視角，先選模式再輸入關鍵字，查到的內容會完全不同：",
        bullets: [
          "治具模式：適合追庫存、圖片、收退料紀錄與站點需求",
          "機種模式：適合追站點配置、治具需求與產能分析"
        ],
        placement: "bottom"
      },
      {
        id: "search-input",
        route: "/search/detail",
        target: "[data-tour='search-query-field']",
        title: "查詢欄支援代碼與名稱",
        description: "可輸入治具或機種的編號、代碼、名稱，查到後再決定要看哪個區塊。",
        placement: "bottom"
      },
      {
        id: "search-sections",
        route: "/search/detail",
        target: "[data-tour='search-section-chips']",
        title: "查到資料後，用區塊籤控制畫面內容",
        description: "先開你現在需要的區塊，其餘隨時可以切換：",
        bullets: [
          "總覽：基本資訊與目前狀態",
          "圖片：治具或機種相關照片",
          "datecode/編號庫存：目前庫存明細",
          "收退料：這筆資料的歷史異動紀錄",
          "相關機種／站點詳細：關聯資料",
          "資料維護：修改主資料本身"
        ],
        placement: "bottom"
      }
    ]
  },
  {
    id: "inventory-workflow",
    sectionLabel: "收退料",
    label: "批次收 / 退料 & 收退料總檢視",
    summary: "同一套教學先走批次收退料，再接到歷史總檢視與篩選查詢。",
    requiresInventoryAccess: true,
    steps: [
      {
        id: "inventory-entry",
        route: "/search",
        target: "[data-tour='inventory-entry-trigger']",
        title: "收退料從這個全域入口開啟",
        description: "從首頁頂部直接開啟，不用先切頁就能處理批次資料。",
        placement: "bottom"
      },
      {
        id: "inventory-mode",
        route: "/search",
        target: "[data-tour='inventory-batch-panel'] [data-tour='inventory-mode-switch']",
        title: "先切換收料或退料模式",
        description: "收料會加庫存，退料會扣庫存；單號與備註會一併記錄。",
        note: {
          tone: "warning",
          text: "方向選錯會讓庫存往反方向變動，貼資料前再確認一次。"
        },
        placement: "bottom",
        openBatchModal: true
      },
      {
        id: "inventory-source",
        route: "/search",
        target: "[data-tour='inventory-batch-panel'] [data-tour='detailed-inventory-source']",
        title: "再確認這一批是客供或自購",
        description: "來源會套用到本批全部明細，預設為客供；只有公司自行採購的治具才切成自購。",
        note: {
          tone: "warning",
          text: "來源選錯會讓客供／自購庫存拆分不正確，送出前請和單據確認。"
        },
        placement: "bottom",
        openBatchModal: true
      },
      {
        id: "inventory-batch-panel",
        route: "/search",
        target: "[data-tour='inventory-batch-panel']",
        title: "整個批次操作都在這個面板完成",
        description: "上方填單號備註，中間貼資料，下方看解析結果，全程不用切頁。",
        placement: "right",
        openBatchModal: true
      },
      {
        id: "inventory-paste-format",
        route: "/search",
        target: "[data-tour='inventory-batch-panel'] [data-tour='inventory-paste-field']",
        title: "批次貼上支援兩種格式",
        description: "這個欄位可直接貼上，也可以按 Tab 輸入分隔：",
        bullets: [
          "兩行一組：第一行治具代碼-datecode/編號，第二行數量",
          "單行表格式：治具代碼、datecode/編號、數量用 Tab 分開",
          "1-4 碼純數字會自動左補零成 4 碼，其餘保留原樣"
        ],
        example: [
          { label: "兩行格式", value: "JIG-0012-0088\n5" },
          { label: "TAB 格式", value: "JIG-0012\t0088\t5" }
        ],
        placement: "left",
        openBatchModal: true
      },
      {
        id: "inventory-preview",
        route: "/search",
        target: "[data-tour='inventory-batch-panel'] [data-tour='inventory-preview-table']",
        title: "貼上後先看解析預覽，不要直接送出",
        description: "系統會把每一列拆成治具、datecode/編號、數量與狀態，先確認每一列的狀態再考慮送出：",
        bullets: [
          "ready：格式正確，會被實際送出",
          "error：原始格式有問題，需要先修正這一列",
          "needs-confirm / needs-add：治具尚未確認，見下一步說明"
        ],
        placement: "top",
        openBatchModal: true
      },
      {
        id: "inventory-missing-fixture",
        route: "/search",
        target: "[data-tour='inventory-batch-panel'] [data-tour='inventory-preview-table']",
        title: "收料遇到沒建過的治具，要先決定怎麼處理",
        description: "系統會依相似程度分成兩種情況，處理方式不同：",
        bullets: [
          "needs-confirm（找到相近代碼）：按「同一治具」採用既有治具，或改為新增",
          "needs-add（完全找不到）：按「新增治具」現場建立，或先「略過」這一列"
        ],
        placement: "top",
        openBatchModal: true
      },
      {
        id: "inventory-submit",
        route: "/search",
        target: "[data-tour='inventory-batch-panel'] [data-tour='inventory-submit-action']",
        title: "確認單號與待處理列都清乾淨後再送出",
        description: "還有 needs-confirm、needs-add 或 error 時系統不會放行，處理完才能送出。",
        note: {
          tone: "warning",
          text: "送出即寫入正式紀錄與庫存，無法一鍵復原，請先核對單號與數量。"
        },
        placement: "top",
        openBatchModal: true
      },
      {
        id: "inventory-export-entry",
        route: "/search",
        target: "[data-tour='inventory-export-entry-trigger']",
        title: "所有常用匯出都走同一個匯出中心",
        description: "當你不是要立即收退料，而是要整理資料交給現場、主管或其他部門時，直接走這個全域入口。",
        bullets: [
          "同一入口可匯出收退料、主資料、站點設定、治具需求與治具資料品質",
          "不用記住每個頁面的匯出按鈕位置",
          "目前客戶範圍會一起帶入"
        ],
        placement: "bottom"
      },
      {
        id: "inventory-export-panel",
        route: "/search",
        target: "[data-tour='inventory-export-panel']",
        title: "匯出中心集中處理資料類型、格式與範圍",
        description: "打開後先選資料集，再選格式；如果是收退料資料，還能直接縮日期與條件。",
        placement: "left",
        openExportModal: true
      },
      {
        id: "inventory-export-report-type",
        route: "/search",
        target: "[data-tour='inventory-export-report-type']",
        title: "先選匯出格式",
        description: "不同資料集會提供對應格式：",
        bullets: [
          "收退料資料可選 XLSX 或 TXT",
          "主資料、站點設定、治具需求、治具資料品質目前匯出 CSV"
        ],
        placement: "left",
        openExportModal: true
      },
      {
        id: "inventory-export-scope",
        route: "/search",
        target: "[data-tour='inventory-export-scope-mode']",
        title: "再決定全部資料或自定義範圍",
        description: "目前只有收退料資料支援自定義範圍；其他資料會直接匯出目前客戶的完整內容。",
        placement: "left",
        openExportModal: true
      },
      {
        id: "inventory-export-filters",
        route: "/search",
        target: "[data-tour='inventory-export-filters']",
        title: "收退料明細可依日期、來源與追蹤欄位縮小範圍",
        description: "選擇收退料明細與自定義條件後，可再篩選收／退料、客供／自購、單號、治具與 datecode/編號。",
        bullets: [
          "來源選「客供」只匯出客供明細；選「自購」只匯出自購明細",
          "來源留在「全部」時，不限制客供／自購",
          "多個條件會同時套用，先縮條件可讓檔案更容易核對"
        ],
        placement: "top",
        openExportModal: true
      },
      {
        id: "inventory-export-submit",
        route: "/search",
        target: "[data-tour='inventory-export-submit']",
        title: "最後確認欄位與範圍後再匯出",
        description: "按下確定後會直接下載檔案；若要交給別人核對，建議先確認目前客戶與匯出格式沒有選錯。",
        placement: "top",
        openExportModal: true
      },
      {
        id: "overview-menu",
        route: "/search",
        target: "[data-tour='home-more-menu-trigger']",
        title: "查歷史時改走更多功能的總檢視入口",
        description: "批次收退料是立即作業；要回頭查歷史異動，從這裡進總檢視。",
        placement: "bottom",
        openMoreMenu: true
      },
      {
        id: "overview-entry",
        route: "/search",
        target: "[data-tour='home-overview-entry']",
        title: "從這裡進入收退料總檢視",
        description: "進入專門查歷史收退料的頁面，可查治具、日期、識別碼或單號的過往異動。",
        placement: "left",
        openMoreMenu: true
      },
      {
        id: "overview-page",
        route: "/inventory/overview",
        target: "[data-tour='overview-page-head']",
        title: "總檢視頁面集中看全部歷史記錄",
        description: "先確認客戶與查詢範圍，這是整個客戶的收退料總表，不是單一治具畫面。",
        placement: "bottom"
      },
      {
        id: "overview-filters",
        route: "/inventory/overview",
        target: "[data-tour='overview-filter-form']",
        title: "常用條件與來源篩選都在上方",
        description: "主畫面可依類型、日期與治具查詢；點「進階篩選」後，還能依客供／自購、單號、datecode/編號及操作人員縮小結果。",
        bullets: [
          "來源選「客供」：只看客供明細",
          "來源選「自購」：只看自購明細",
          "重設：清除全部條件；查詢：套用條件並回到第 1 頁"
        ],
        placement: "bottom"
      }
    ]
  },
  {
    id: "master-basics",
    sectionLabel: "主資料維護",
    label: "治具 / 機種 / 站點主資料",
    summary: "沿用目前教學風格，依序帶你看治具、機種、站點三種主資料的切換與維護方式。",
    requiresMasterAccess: true,
    steps: [
      {
        id: "master-menu",
        route: "/search",
        target: "[data-tour='home-more-menu-trigger']",
        title: "主資料維護同樣從更多功能進入",
        description: "維護入口統一收在首頁同一個選單。",
        placement: "bottom",
        openMoreMenu: true
      },
      {
        id: "master-entry",
        route: "/search",
        target: "[data-tour='home-master-entry']",
        title: "點這裡進入資料維護頁",
        description: "維護治具、機種、站點等主資料，其他功能都依賴這裡的資料是否正確。",
        placement: "left",
        openMoreMenu: true
      },
      {
        id: "master-tabs",
        route: "/master/fixtures",
        target: "[data-tour='master-tabs']",
        title: "先在上方切換要維護的主資料類型",
        description: "主資料不是只有治具，這裡會切換三種核心資料：",
        bullets: [
          "治具：管理治具編號、名稱、儲位、最低水位與負責人",
          "機種：管理機種編號與名稱，供查詢與產能設定共用",
          "站點：管理站點編號與名稱，供機種站點對應與治具需求使用"
        ],
        placement: "bottom"
      },
      {
        id: "master-fixture-list",
        route: "/master/fixtures",
        target: "[data-tour='master-list-table']",
        title: "先看治具清單，確認目前有哪些資料",
        description: "治具分頁會列出編號、名稱、水位與儲位；通常先從左側清單找資料，再決定是新增還是修改。",
        placement: "right"
      },
      {
        id: "master-fixture-detail",
        route: "/master/fixtures",
        target: "[data-tour='master-detail-form']",
        title: "治具表單會維護儲位、水位與負責人等完整資訊",
        description: "選到治具後，右側表單可修改治具主檔；這些欄位會直接影響查詢頁、收退料與庫存提醒。",
        placement: "left"
      },
      {
        id: "master-model-tab",
        route: "/master/models",
        target: "[data-tour='master-tabs']",
        title: "切到機種分頁，維護機種主資料",
        description: "機種主資料比治具精簡，重點是把代碼與名稱維持正確，讓搜尋與產能設定可以對到同一套資料。",
        placement: "bottom"
      },
      {
        id: "master-model-detail",
        route: "/master/models",
        target: "[data-tour='master-detail-form']",
        title: "機種表單主要管理編號、名稱與啟用狀態",
        description: "機種建立好之後，後續的機種站點對應與站點治具需求才有正確的主檔可以綁定。",
        placement: "left"
      },
      {
        id: "master-station-tab",
        route: "/master/stations",
        target: "[data-tour='master-tabs']",
        title: "再切到站點分頁，維護站點主資料",
        description: "站點是產能頁的基礎字典；如果站點代碼或名稱不完整，後面的 Mapping 與 Requirement 也會一起出錯。",
        placement: "bottom"
      },
      {
        id: "master-station-detail",
        route: "/master/stations",
        target: "[data-tour='master-detail-form']",
        title: "站點表單完成新增或修改後，一樣要記得儲存",
        description: "站點資料通常只有編號、名稱與狀態，但它會被多個機種與需求設定共用，所以命名要一致。",
        note: {
          tone: "warning",
          text: "沒儲存就切換或離開頁面，修改會直接遺失。"
        },
        placement: "left"
      }
    ]
  },
  {
    id: "production-workflow",
    sectionLabel: "產能管理",
    label: "產能設定與治具需求",
    summary: "選定機種後，在同一畫面完成站點設定，並直接替站點配置治具需求。",
    steps: [
      {
        id: "production-menu",
        route: "/search",
        target: "[data-tour='home-more-menu-trigger']",
        title: "產能管理入口也在更多功能",
        description: "從首頁更多功能進入產能管理，選好機種後直接配置站點與治具需求。",
        placement: "bottom",
        openMoreMenu: true
      },
      {
        id: "production-entry",
        route: "/search",
        target: "[data-tour='home-production-entry']",
        title: "從這裡進入產能管理",
        description: "進去後可看總覽與產能設定；產能設定頁會把站點設定與治具需求整合在同一畫面。",
        placement: "left",
        openMoreMenu: true
      },
      {
        id: "production-tabs",
        route: "/production/mapping",
        target: "[data-tour='production-tabs']",
        title: "產能設定已整合成同一個工作畫面",
        description: "現在不需要理解 Mapping 與 Requirement 的分頁關係，直接進入產能設定即可：",
        bullets: [
          "① 先替目前機種建立會經過的站點",
          "② 再直接替站點配置治具與需求數量"
        ],
        placement: "bottom"
      },
      {
        id: "production-filter-row",
        route: "/production/mapping",
        target: "[data-tour='production-filter-row']",
        title: "進來先選機種，再進行下面的配置",
        description: "上方選機種，決定你在編輯哪一個；切換機種後清單與表單會一起更新。",
        placement: "bottom"
      },
      {
        id: "production-mapping-panel",
        route: "/production/mapping",
        target: "[data-tour='production-mapping-panel']",
        title: "左側先選擇這個機種的站點",
        description: "同一機種可對應多個站點；點選整列站點，右側就會切換到該站點的治具需求。",
        placement: "top"
      },
      {
        id: "production-mapping-form",
        route: "/production/mapping",
        target: "[data-tour='production-mapping-form']",
        title: "機種會自動沿用，只需選擇站點",
        description: "上方已選好的機種會自動帶入。搜尋站點編號或名稱後，按「加入站點」即可。",
        example: [{ label: "站點代碼", value: "ST-05" }],
        placement: "top"
      },
      {
        id: "production-mapping-list",
        route: "/production/mapping",
        target: "[data-tour='production-mapping-list']",
        title: "整列點選站點，右側直接接續配置",
        description: "清單同時顯示站點名稱與最大開站數；尚未配置治具的站點會標示「待配置」。",
        placement: "top"
      },
      {
        id: "production-requirements-filter-row",
        route: "/production/mapping",
        target: "[data-tour='production-filter-row']",
        title: "機種不需要重選，直接在同頁往下配置治具",
        description: "同一個機種會一路帶到治具需求區，所以只要專注目前機種與目前站點即可。",
        placement: "bottom"
      },
      {
        id: "production-requirement-panel",
        route: "/production/mapping",
        target: "[data-tour='production-requirement-panel']",
        title: "右側直接替目前站點配置治具需求",
        description: "每筆需求代表某機種在某站點需要幾套治具；右側會同步顯示庫存、可開站數與限制治具。",
        placement: "top"
      },
      {
        id: "production-requirement-form",
        route: "/production/mapping",
        target: "[data-tour='production-requirement-form']",
        title: "站點已固定，只需選治具與數量",
        description: "從左側選定站點後，這裡只剩兩個必要輸入：",
        bullets: [
          "① 搜尋治具編號或名稱",
          "② 填入每開一站需要的數量",
          "③ 儲存前先查看最大開站數預估"
        ],
        example: [{ label: "需求數量", value: "3" }],
        placement: "top"
      },
      {
        id: "production-requirement-list",
        route: "/production/mapping",
        target: "[data-tour='production-requirement-list']",
        title: "新增後在列表核對站點、治具與數量",
        description: "下方是該站點的正式需求清單，可直接編輯；大量新增用批次貼上。",
        placement: "top"
      }
    ]
  },
  {
    id: "system-detailed-guide",
    sectionLabel: "完整詳細版",
    label: "全系統按鈕與操作說明",
    summary: "逐頁說明首頁、匯出中心、收退料、總檢視、主資料與產能管理的主要按鈕，適合第一次完整認識系統。",
    requiresInventoryAccess: true,
    requiresMasterAccess: true,
    steps: [
      {
        id: "detailed-home",
        route: "/search",
        target: "[data-tour='detailed-home-button']",
        title: "Jig Record 標誌：回首頁",
        description: "不論目前在哪一頁，按左上角 Jig Record 標誌都會回到治具／機種查詢首頁。",
        placement: "bottom"
      },
      {
        id: "detailed-primary-actions",
        route: "/search",
        target: "[data-tour='detailed-primary-actions']",
        title: "三個主要功能按鈕",
        description: "這三個按鈕是日常最常用的入口：",
        bullets: [
          "治具收／退料：開啟批次作業視窗，增加或扣除庫存",
          "匯出中心：下載收退料、主資料、站點設定、治具需求或品質資料",
          "新手教學：回到教學選單，可改看其他精簡版或這套詳細版"
        ],
        placement: "bottom"
      },
      {
        id: "detailed-export-panel",
        route: "/search",
        target: "[data-tour='inventory-export-panel']",
        title: "匯出中心視窗與關閉按鈕",
        description: "匯出中心會保留目前客戶範圍；右上「關閉」與下方「取消」都只關閉視窗，不會下載或修改資料。",
        placement: "left",
        openExportModal: true
      },
      {
        id: "detailed-export-dataset",
        route: "/search",
        target: "[data-tour='detailed-export-dataset']",
        title: "匯出資料：選擇要下載的資料集",
        description: "點選任一資料卡即可切換內容：",
        bullets: [
          "收退料摘要：依治具彙總收料、退料與結餘",
          "收退料明細：依治具與 datecode/編號彙總，可使用進階篩選",
          "治具／機種／站點／站點設定／治具需求：匯出目前客戶的對應主資料",
          "治具資料品質：Admin 可下載缺漏與異常清單"
        ],
        placement: "left",
        openExportModal: true
      },
      {
        id: "detailed-export-format",
        route: "/search",
        target: "[data-tour='inventory-export-report-type']",
        title: "匯出格式：XLSX、TXT 或 CSV",
        description: "XLSX 適合用試算表開啟；TXT 適合純文字或系統交換。主資料類資料集會自動使用 CSV，不需要另外選格式。",
        placement: "left",
        openExportModal: true
      },
      {
        id: "detailed-export-scope",
        route: "/search",
        target: "[data-tour='inventory-export-scope-mode']",
        title: "資料範圍：全部或自定義條件",
        description: "「全部」下載目前客戶的完整收退料資料；「自定義條件」展開進階篩選。其他主資料會直接匯出目前客戶全部資料。",
        placement: "left",
        openExportModal: true
      },
      {
        id: "detailed-export-filters",
        route: "/search",
        target: "[data-tour='inventory-export-filters']",
        title: "進階篩選：每個欄位的用途",
        description: "教學已自動切到收退料明細與自定義條件。留空代表不限制；同時填入時會一起套用：",
        bullets: [
          "日期（起／迄）：限制交易發生日期",
          "交易類型：只看收料或只看退料",
          "來源：只看客供或自購",
          "單號：依交易單號縮小範圍",
          "治具編號：可用完整或部分編號查找",
          "datecode/編號：依該批識別碼查找"
        ],
        placement: "left",
        openExportModal: true
      },
      {
        id: "detailed-export-source",
        route: "/search",
        target: "[data-tour='detailed-export-source']",
        title: "來源選單：全部、客供、自購",
        description: "選「客供」只匯出客戶提供的收退料明細；選「自購」只匯出公司採購的明細；選「全部」則兩種來源都保留。",
        placement: "left",
        openExportModal: true
      },
      {
        id: "detailed-export-columns",
        route: "/search",
        target: "[data-tour='detailed-export-columns']",
        title: "預計匯出欄位：下載前確認內容結構",
        description: "這些欄位標籤只是預覽，不是按鈕；切換資料集後會同步更新，方便下載前確認檔案是否符合用途。",
        placement: "top",
        openExportModal: true
      },
      {
        id: "detailed-export-actions",
        route: "/search",
        target: "[data-tour='inventory-export-submit']",
        title: "取消與開始匯出按鈕",
        description: "「取消」關閉視窗且不下載；「開始匯出」依目前資料集、格式、範圍與篩選條件建立檔案，完成後會自動下載。",
        placement: "top",
        openExportModal: true
      },
      {
        id: "detailed-status-actions",
        route: "/search",
        target: "[data-tour='detailed-status-actions']",
        title: "登入資訊與三個即時狀態按鈕",
        description: "姓名僅顯示目前登入者；其餘三個膠囊按鈕都可以點開：",
        bullets: [
          "今日收料：查看最近 10 筆收料",
          "今日退料：查看最近 10 筆退料",
          "低水位：查看庫存不足治具，並可直接開啟該治具的收／退料"
        ],
        placement: "bottom"
      },
      {
        id: "detailed-customer",
        route: "/search",
        target: "[data-tour='global-customer-picker']",
        title: "客戶選擇：切換整個系統的資料範圍",
        description: "切換後，查詢、庫存、主資料與產能都會改成該客戶的資料；有未送出草稿時系統會先提醒。",
        note: {
          tone: "warning",
          text: "開始作業前先確認客戶，避免把資料登記到錯誤客戶。"
        },
        placement: "bottom"
      },
      {
        id: "detailed-more-menu",
        route: "/search",
        target: "[data-tour='home-more-menu-trigger']",
        title: "更多功能：開啟三個專用工作頁",
        description: "按下後會看到：",
        bullets: [
          "收退料總檢視：查完整歷史明細",
          "資料維護：管理治具、機種、站點與權限內的主資料",
          "產能管理：查看產能總覽、站點與治具需求設定"
        ],
        placement: "bottom",
        openMoreMenu: true
      },
      {
        id: "detailed-logout",
        route: "/search",
        target: "[data-tour='detailed-logout-button']",
        title: "登出：結束目前登入狀態",
        description: "共用電腦作業完成後請按登出，避免下一位使用者沿用你的權限。",
        placement: "bottom"
      },
      {
        id: "detailed-search-controls",
        route: "/search/detail",
        target: "[data-tour='detailed-search-controls']",
        title: "查詢列的每個按鈕",
        description: "先選資料類型，再輸入代碼或名稱：",
        bullets: [
          "治具：搜尋治具、庫存與收退料紀錄",
          "機種：搜尋機種、站點與需求資料",
          "搜尋：送出目前關鍵字；鍵盤 Enter 也可以",
          "×：清空搜尋欄與目前結果；鍵盤 Esc 也可以"
        ],
        placement: "bottom"
      },
      {
        id: "detailed-search-sections",
        route: "/search/detail",
        target: "[data-tour='search-section-chips']",
        title: "結果區塊按鈕：決定畫面要顯示什麼",
        description: "每個按鈕都是顯示／隱藏切換，不會修改資料：",
        bullets: [
          "總覽、圖片：顯示基本資料與圖片",
          "datecode/編號庫存、收退料：顯示庫存拆分與歷史",
          "相關機種、站點詳細、需求明細：顯示關聯設定",
          "資料維護：顯示可編輯的主資料表單"
        ],
        placement: "bottom"
      },
      {
        id: "detailed-inventory-mode",
        route: "/search",
        target: "[data-tour='inventory-batch-panel'] [data-tour='inventory-mode-switch']",
        title: "收料／退料按鈕：決定庫存增減方向",
        description: "收料會增加庫存，退料會扣除該治具與 datecode/編號的庫存。",
        note: {
          tone: "warning",
          text: "這是整批設定，切換後會套用到所有待送出明細。"
        },
        placement: "bottom",
        openBatchModal: true
      },
      {
        id: "detailed-inventory-source",
        route: "/search",
        target: "[data-tour='inventory-batch-panel'] [data-tour='detailed-inventory-source']",
        title: "客供／自購按鈕：決定本批庫存來源",
        description: "客供是客戶提供；自購是公司自行採購。來源會套用到整批明細，並影響客供／自購庫存統計。",
        placement: "bottom",
        openBatchModal: true
      },
      {
        id: "detailed-inventory-meta",
        route: "/search",
        target: "[data-tour='inventory-batch-panel'] [data-tour='detailed-inventory-meta']",
        title: "單號與備註欄位",
        description: "單號是必填的追蹤依據；備註可補充工單、異常原因或現場說明。來源按鈕也在這一區。",
        placement: "bottom",
        openBatchModal: true
      },
      {
        id: "detailed-inventory-paste",
        route: "/search",
        target: "[data-tour='inventory-batch-panel'] [data-tour='inventory-paste-field']",
        title: "批次內容：貼上待處理資料",
        description: "貼上後系統會立即解析。可使用兩行格式或 Tab 表格格式，不需要另外按解析按鈕。",
        example: [
          { label: "兩行格式", value: "JIG-0012-0088\n5" },
          { label: "TAB 格式", value: "JIG-0012\t0088\t5" }
        ],
        placement: "left",
        openBatchModal: true
      },
      {
        id: "detailed-inventory-actions",
        route: "/search",
        target: "[data-tour='inventory-batch-panel'] [data-tour='detailed-inventory-actions']",
        title: "批次面板的動作按鈕",
        description: "送出前請先看待處理與錯誤數量：",
        bullets: [
          "套用教學試跑：只在教學模式出現，帶入範例且不寫正式資料",
          "清空：移除單號、備註與目前批次內容",
          "送出收料／送出退料：寫入正式交易與庫存；有錯誤列時會停用",
          "查看正常列／收合正常列：展開或隱藏解析成功的明細"
        ],
        placement: "top",
        openBatchModal: true
      },
      {
        id: "detailed-overview-filters",
        route: "/inventory/overview",
        target: "[data-tour='overview-filter-form']",
        title: "總檢視主篩選：先縮小常用範圍",
        description: "類型、起始日期、結束日期、治具編號是最常用條件；輸入完成後按下方「查詢」。",
        placement: "bottom"
      },
      {
        id: "detailed-overview-advanced",
        route: "/inventory/overview",
        target: "[data-tour='overview-advanced-toggle']",
        title: "進階篩選按鈕：展開更多查詢條件",
        description: "展開後可選客供／自購來源，並依單號、datecode/編號、操作人員查詢；再次按下可收合。",
        placement: "bottom"
      },
      {
        id: "detailed-overview-actions",
        route: "/inventory/overview",
        target: "[data-tour='overview-filter-actions']",
        title: "重設與查詢按鈕",
        description: "重設會清空所有條件並回到預設頁；查詢會套用目前條件、更新網址並回到第 1 頁。",
        placement: "top"
      },
      {
        id: "detailed-overview-pager",
        route: "/inventory/overview",
        target: "[data-tour='overview-pager']",
        title: "分頁區的每個按鈕",
        description: "大量歷史資料不會一次全部載入：",
        bullets: [
          "每頁：切換一次顯示 50 或 100 筆",
          "上一頁／下一頁：依目前篩選條件前後翻頁",
          "跳至＋跳轉：直接輸入頁碼前往指定頁"
        ],
        placement: "top"
      },
      {
        id: "detailed-master-tabs",
        route: "/master/fixtures",
        target: "[data-tour='master-tabs']",
        title: "資料維護分頁按鈕",
        description: "治具、機種、站點切換核心主資料；Admin 另外可看到客戶、使用者、帳目管理與資料品質。",
        placement: "bottom"
      },
      {
        id: "detailed-master-list",
        route: "/master/fixtures",
        target: "[data-tour='master-list-toolbar']",
        title: "主資料清單的搜尋、狀態與新增",
        description: "搜尋欄即時縮小清單；狀態選單切換全部／啟用／停用；「＋新增」會清空右側表單進入新增模式。",
        placement: "right"
      },
      {
        id: "detailed-master-detail",
        route: "/master/fixtures",
        target: "[data-tour='detailed-master-detail']",
        title: "詳細資料上方的新增與重載",
        description: "新增會開始建立新資料；重載會放棄畫面尚未儲存的內容，重新讀取目前選取資料。",
        placement: "left"
      },
      {
        id: "detailed-master-form-actions",
        route: "/master/fixtures",
        target: "[data-tour='master-form-actions']",
        title: "主資料表單下方按鈕",
        description: "儲存寫入目前欄位；取消回到新增模式；停用／啟用改變資料狀態。Admin 看到的永久刪除會另外要求確認。",
        note: {
          tone: "warning",
          text: "永久刪除與停用不同；永久刪除前請確認歷史資料保留方式。"
        },
        placement: "top"
      },
      {
        id: "detailed-production-tabs",
        route: "/production/mapping",
        target: "[data-tour='production-tabs']",
        title: "產能管理的總覽／產能設定按鈕",
        description: "總覽用來看各站點可開站數；產能設定用來修改機種站點與治具需求。",
        placement: "bottom"
      },
      {
        id: "detailed-production-filter",
        route: "/production/mapping",
        target: "[data-tour='production-filter-row']",
        title: "機種選擇與限制治具按鈕",
        description: "機種選單切換目前查看或編輯的機種；總覽中的限制治具卡片可直接定位造成瓶頸的治具。",
        placement: "bottom"
      },
      {
        id: "detailed-production-mapping",
        route: "/production/mapping",
        target: "[data-tour='production-mapping-panel']",
        title: "機種站點設定區的按鈕",
        description: "加入站點會把選取站點加入目前機種；點站點整列會切換右側需求；編輯／移除用來維護既有對應。",
        placement: "top"
      },
      {
        id: "detailed-production-requirements",
        route: "/production/mapping",
        target: "[data-tour='production-requirement-panel']",
        title: "治具需求區的按鈕",
        description: "加入治具／儲存變更寫入每站需求；取消放棄編輯；複製此站設定與批次匯入適合大量建立；清單中的編輯／刪除維護單筆需求。",
        placement: "top"
      }
    ]
  },
  {
    id: "admin-inventory-governance",
    sectionLabel: "系統管理",
    label: "收退料帳目管理 / 治具資料品質",
    summary: "Admin 用來修復資料與追查異常的兩個分頁：先看帳目，再看品質。",
    requiresMasterAccess: true,
    requiresAdminAccess: true,
    steps: [
      {
        id: "admin-ledger-tab",
        route: "/master/ledger",
        target: "[data-tour='master-tab-ledger']",
        title: "帳目管理用來追交易與處理撤回 / 重算",
        description: "這不是一般查詢頁，而是 admin 的修復入口；遇到異常帳目、重複收退料或庫存不一致時從這裡進。",
        placement: "bottom"
      },
      {
        id: "admin-ledger-list",
        route: "/master/ledger",
        target: "[data-tour='master-ledger-list']",
        title: "左側清單集中列出案件，先選案再處理",
        description: "可先用單號、操作人、治具編號與交易類型縮小範圍，再從清單挑一筆案件。",
        placement: "right"
      },
      {
        id: "admin-ledger-filters",
        route: "/master/ledger",
        target: "[data-tour='master-ledger-filters']",
        title: "篩選列是追查異常的第一步",
        description: "不知道是哪一筆出錯時，先縮日期、單號或操作人，再決定要看明細、撤回或重算。",
        placement: "bottom"
      },
      {
        id: "admin-ledger-detail",
        route: "/master/ledger",
        target: "[data-tour='master-ledger-detail']",
        title: "右側明細提供重載、全量重算與撤回案件",
        description: "選中案件後，右側可看明細、重載、重算整體庫存摘要，或撤回這筆案件。",
        note: {
          tone: "warning",
          text: "撤回與重算都會直接影響正式庫存，操作前請先確認單號與明細是否正確。"
        },
        placement: "left"
      },
      {
        id: "admin-quality-tab",
        route: "/master/quality",
        target: "[data-tour='master-tab-quality']",
        title: "治具資料品質分頁集中看主檔缺漏與庫存異常",
        description: "當問題不一定來自交易，而是主資料不完整時，改從這個分頁盤點名稱、儲位、圖片與關聯缺漏。",
        placement: "bottom"
      },
      {
        id: "admin-quality-summary",
        route: "/master/quality",
        target: "[data-tour='master-quality-summary']",
        title: "先用上方摘要看異常分布，再決定優先順序",
        description: "摘要卡會把沒有名稱、沒有圖片、缺少關聯與庫存不一致分開統計，方便決定先補哪一類。",
        placement: "bottom"
      },
      {
        id: "admin-quality-panel",
        route: "/master/quality",
        target: "[data-tour='master-quality-panel']",
        title: "點問題標籤可直接開啟修正流程",
        description: "多數問題都能在這頁直接修，不必自己再跳分頁；像缺圖片、缺名稱、缺儲位都能就地處理。",
        bullets: [
          "主檔欄位缺漏：直接在品質表格內補值並更新",
          "缺機種關聯：直接跳到產能管理的治具需求區補資料",
          "庫存不一致：回到帳目管理做撤回或重算"
        ],
        placement: "top"
      }
    ]
  }
];

export const onboardingFlowMap = new Map(onboardingFlows.map((flow) => [flow.id, flow]));

export function getOnboardingFlow(flowId: OnboardingFlowId | null): OnboardingFlow | null {
  if (!flowId) {
    return null;
  }
  return onboardingFlowMap.get(flowId) ?? null;
}
