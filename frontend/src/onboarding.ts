export type TourPlacement = "top" | "bottom" | "left" | "right";

export type OnboardingFlowId =
  | "guest-search-report"
  | "guest-readonly-guide"
  | "search-basics"
  | "report-basics"
  | "inventory-workflow"
  | "master-basics"
  | "production-workflow"
  | "system-detailed-guide"
  | "admin-inventory-governance"
  | "form-guest-quick-guide"
  | "form-guest-detailed-guide"
  | "form-quick-guide"
  | "form-detailed-guide"
  | "form-admin-user-access"
  | "workbench-guest-quick-guide"
  | "workbench-guest-detailed-guide"
  | "workbench-quick-guide"
  | "workbench-detailed-guide";

export type OnboardingSurface = "modern" | "form" | "workbench";
export type OnboardingVariant = "concise" | "detailed";

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
  /** 只在 Admin 播放的步驟；用於同一份完整教學中的管理專區。 */
  requiresAdminAccess?: boolean;
  /** 只在 Super Admin 播放的客戶／使用者管理步驟。 */
  requiresSuperAdminAccess?: boolean;
}

export interface OnboardingFlow {
  id: OnboardingFlowId;
  sectionLabel: string;
  label: string;
  summary: string;
  requiresInventoryAccess?: boolean;
  requiresMasterAccess?: boolean;
  requiresAdminAccess?: boolean;
  requiresSuperAdminAccess?: boolean;
  guestOnly?: boolean;
  surface?: OnboardingSurface;
  variant?: OnboardingVariant;
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
        description: "預設只顯示已啟用治具，也可切換已停用或所有治具；另可依機種、站點、水位、儲位與今日／指定日期收退料縮小範圍。",
        placement: "bottom"
      },
      {
        id: "guest-report-capacity",
        route: "/search",
        query: { home_mode: "report" },
        target: "[data-tour='report-capacity-trigger']",
        title: "選好機種後計算各站點最大開站數",
        description: "只選機種並保留「全部站點」會列出所有已綁定站點；再指定站點則只計算該站。點「查看治具明細」會展開需求、庫存、此治具可支援站數與瓶頸報表。",
        placement: "bottom"
      },
      {
        id: "guest-report-results",
        route: "/search",
        query: { home_mode: "report" },
        target: "[data-tour='report-result-table']",
        title: "報表支援圖片、欄位精簡與完整篩選匯出",
        description: "點治具代碼可看圖片；空欄會依整批篩選結果自動隱藏，也能自行勾選欄位。匯出會包含全部符合篩選的資料，而不只目前頁。",
        placement: "top"
      }
    ]
  },
  {
    id: "guest-readonly-guide",
    sectionLabel: "完整唯讀教學",
    label: "訪客可查看功能完整說明",
    summary: "逐步認識查詢、報表、匯出、即時狀態與收退料總檢視；全程只介紹訪客可查看的功能，不會修改正式資料。",
    guestOnly: true,
    steps: [
      {
        id: "guest-readonly-home-switch",
        route: "/search",
        query: { home_mode: "query" },
        target: "[data-tour='home-mode-switch']",
        title: "首頁包含查詢與報表兩種唯讀工作模式",
        description: "訪客預設進入報表，也能隨時切到查詢工作台；兩邊共用目前選擇的客戶與查詢內容。",
        placement: "bottom"
      },
      {
        id: "guest-readonly-search-mode",
        route: "/search",
        query: { home_mode: "query" },
        target: "[data-tour='search-mode-switch']",
        title: "查詢工作台可依治具或機種切換視角",
        description: "治具視角用來看庫存、圖片與關聯；機種視角用來看站點、所需治具與配置內容。",
        placement: "bottom"
      },
      {
        id: "guest-readonly-search-input",
        route: "/search",
        query: { home_mode: "query" },
        target: "[data-tour='search-query-field']",
        title: "輸入代碼或名稱查找資料",
        description: "輸入完整或部分治具／機種代碼與名稱，選取結果後即可檢視詳細內容；切換到報表時會保留查詢值。",
        placement: "bottom"
      },
      {
        id: "guest-readonly-report-switch",
        route: "/search",
        query: { home_mode: "report" },
        target: "[data-tour='home-mode-switch']",
        title: "報表模式適合一次盤點多筆庫存與配置",
        description: "報表會整合治具、機種、站點、庫存與收退料資訊，可依工作情境自由縮小範圍。",
        placement: "bottom"
      },
      {
        id: "guest-readonly-report-filters",
        route: "/search",
        query: { home_mode: "report" },
        target: "[data-tour='report-filter-panel']",
        title: "聯動篩選會依選取順序縮小後續選項",
        description: "預設篩選已啟用治具，可切換已停用或所有治具；其他條件依選取順序聯動，修改後需按「套用條件」。",
        placement: "bottom"
      },
      {
        id: "guest-readonly-report-capacity",
        route: "/search",
        query: { home_mode: "report" },
        target: "[data-tour='report-capacity-trigger']",
        title: "最大開站數只依已套用的機種與站點計算",
        description: "選定機種後可計算全部站點，或再指定單一站點；每站治具明細預設收合，點擊後以表格列出需求、庫存、此治具可支援站數與瓶頸。",
        placement: "bottom"
      },
      {
        id: "guest-readonly-report-results",
        route: "/search",
        query: { home_mode: "report" },
        target: "[data-tour='report-result-table']",
        title: "結果表支援圖片、欄位自動精簡與完整篩選匯出",
        description: "點治具代碼可看圖片；整批結果沒有資料的欄位會自動隱藏，仍可保存自己的欄位偏好，也可匯出全部符合目前篩選的資料。",
        placement: "top"
      },
      {
        id: "guest-readonly-export-entry",
        route: "/search",
        target: "[data-tour='inventory-export-panel']",
        title: "匯出中心提供多種唯讀資料下載",
        description: "訪客可以下載權限內的收退料、治具、機種、站點與配置資料；開啟或關閉視窗都不會修改系統資料。",
        placement: "left",
        openExportModal: true
      },
      {
        id: "guest-readonly-export-dataset",
        route: "/search",
        target: "[data-tour='detailed-export-dataset']",
        title: "先選擇要匯出的資料集",
        description: "收退料摘要適合看彙總，收退料明細適合追單號與 datecode／序號；其他選項可下載各類主資料與配置。",
        placement: "left",
        openExportModal: true
      },
      {
        id: "guest-readonly-export-format",
        route: "/search",
        target: "[data-tour='inventory-export-report-type']",
        title: "依使用情境選擇 XLSX、TXT 或 CSV",
        description: "XLSX 適合一般報表檢視，TXT／CSV 適合交換或後續處理；實際可選格式會依資料集調整。",
        placement: "left",
        openExportModal: true
      },
      {
        id: "guest-readonly-export-scope",
        route: "/search",
        target: "[data-tour='inventory-export-scope-mode']",
        title: "收退料資料可選全部或自定義條件",
        description: "自定義條件可限制日期、類型、來源、單號、治具及 datecode／序號，下載前可先確認預計欄位。",
        placement: "left",
        openExportModal: true
      },
      {
        id: "guest-readonly-status",
        route: "/search",
        target: "[data-tour='detailed-status-actions']",
        title: "頂欄可快速查看今日收料、今日退料與低水位",
        description: "三個即時狀態都能展開查看摘要，並可再前往報表或總檢視追查完整資料。",
        placement: "bottom"
      },
      {
        id: "guest-readonly-customer",
        route: "/search",
        target: "[data-tour='global-customer-picker']",
        title: "客戶選擇器會切換整個唯讀資料範圍",
        description: "查詢、報表、匯出與總檢視都會跟著目前客戶更新，開始查找前請先確認客戶。",
        placement: "bottom"
      },
      {
        id: "guest-readonly-more-menu",
        route: "/search",
        target: "[data-tour='workspace-overview-entry']",
        title: "快速作業提供收退料總檢視",
        description: "訪客可從第四個分頁進入唯讀總檢視；收退料操作、資料維護與產能設定需以 User 或 Admin 登入。",
        placement: "bottom"
      },
      {
        id: "guest-readonly-overview-filters",
        route: "/inventory/overview",
        target: "[data-tour='overview-filter-form']",
        title: "收退料總檢視可查完整歷史明細",
        description: "可依收／退料類型、日期與治具編號縮小範圍，再使用進階條件查來源、單號、datecode／序號與操作人員。",
        placement: "bottom"
      },
      {
        id: "guest-readonly-overview-actions",
        route: "/inventory/overview",
        target: "[data-tour='overview-filter-actions']",
        title: "重設與查詢只會更新目前檢視條件",
        description: "查詢會套用條件並回到第 1 頁；重設會清空條件，不會刪除或修改任何收退料資料。",
        placement: "top"
      },
      {
        id: "guest-readonly-overview-pager",
        route: "/inventory/overview",
        target: "[data-tour='overview-pager']",
        title: "使用分頁瀏覽大量歷史資料",
        description: "可切換每頁筆數、前後翻頁或直接跳到指定頁，所有操作都會保留目前篩選範圍。",
        placement: "top"
      },
      {
        id: "guest-readonly-logout",
        route: "/search",
        target: "[data-tour='detailed-logout-button']",
        title: "檢視完成後安全登出",
        description: "在共用電腦完成查詢後請登出，避免下一位使用者沿用目前客戶與瀏覽狀態。",
        placement: "bottom"
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
    id: "report-basics",
    sectionLabel: "首頁報表",
    label: "庫存配置報表",
    summary: "從聯動篩選、套用條件到欄位精簡、產能計算與完整結果匯出。",
    steps: [
      {
        id: "report-home-mode",
        route: "/search",
        query: { home_mode: "report" },
        target: "[data-tour='home-mode-switch']",
        title: "先切到報表模式",
        description: "首頁可在查詢與報表間切換；報表適合一次檢視多筆治具庫存、機種、站點與配置狀態。",
        placement: "bottom"
      },
      {
        id: "report-filter-basics",
        route: "/search",
        query: { home_mode: "report" },
        target: "[data-tour='report-filter-panel']",
        title: "依實際工作順序選擇聯動條件",
        description: "治具狀態預設為已啟用，也可切到已停用或所有治具；其餘條件依選擇順序聯動，第一個欄位優先限制後續選項。",
        placement: "bottom"
      },
      {
        id: "report-apply-filters",
        route: "/search",
        query: { home_mode: "report" },
        target: "[data-tour='report-filter-actions']",
        title: "修改條件後按「套用條件」",
        description: "尚未套用的草稿條件會另外提示；按下後才更新表格、結果數量與網址。重設只會清空篩選，不會修改正式資料。",
        placement: "top"
      },
      {
        id: "report-capacity",
        route: "/search",
        query: { home_mode: "report" },
        target: "[data-tour='report-capacity-trigger']",
        title: "選定機種後計算最大開站數",
        description: "站點保留全部時會計算所有已綁定站點；指定站點時只算單站。點擊各站可展開治具需求、目前庫存、此治具可支援站數與瓶頸表格。",
        placement: "bottom"
      },
      {
        id: "report-columns",
        route: "/search",
        query: { home_mode: "report" },
        target: "[data-tour='report-column-trigger']",
        title: "選擇欄位，空欄由系統自動精簡",
        description: "可套用現場庫存、配置檢查或完整報表預設，也能逐欄勾選。整批篩選結果都沒有資料的欄位會暫時隱藏，有資料時自動恢復。",
        placement: "bottom"
      },
      {
        id: "report-export",
        route: "/search",
        query: { home_mode: "report" },
        target: "[data-tour='report-export-trigger']",
        title: "匯出全部符合篩選的資料",
        description: "可選 XLSX 或 CSV；匯出範圍是目前條件下的完整結果，不只當前頁，欄位則與畫面實際顯示一致。",
        placement: "bottom"
      },
      {
        id: "report-results",
        route: "/search",
        query: { home_mode: "report" },
        target: "[data-tour='report-result-table']",
        title: "從結果表查看圖片與收退料明細",
        description: "點治具代碼可開啟圖片；若套用收料或退料條件，結果工具列會出現「展示收／退料明細」，可查看日期、單號、編號、來源與數量。",
        placement: "top"
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
        title: "直接在資料方格輸入或貼上",
        description: "每一欄都已固定分區，可逐格輸入，也可把 Excel／其他表格的多列資料直接貼到第一格：",
        bullets: [
          "欄位順序：治具、datecode/編號、數量",
          "快速新增與大量貼上共用同一個方格，不需要整理文字格式",
          "也能辨識治具編號-datecode 與下一行數量的直式清單，以及含日期／名稱／不良現象的表格標題",
          "1-4 碼純數字會自動左補零成 4 碼，其餘保留原樣"
        ],
        example: [
          { label: "方格第 1 列", value: "JIG-0012　0088　5" },
          { label: "可連續貼上", value: "JIG-0013　0089　2" }
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
        id: "overview-entry",
        route: "/search",
        target: "[data-tour='workspace-overview-entry']",
        title: "從這裡進入收退料總檢視",
        description: "進入專門查歷史收退料的頁面，可查治具、日期、識別碼或單號的過往異動。",
        placement: "bottom"
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
        description: "每筆需求代表某機種在某站點需要幾套治具；右側會同步顯示庫存、此治具可支援站數與限制治具。",
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
    summary: "逐頁說明首頁查詢、庫存配置報表、匯出中心、收退料、總檢視、主資料與產能管理，適合第一次完整認識系統。",
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
        id: "detailed-report-mode",
        route: "/search",
        query: { home_mode: "report" },
        target: "[data-tour='home-mode-switch']",
        title: "首頁報表：切換到庫存配置報表",
        description: "報表模式把治具、庫存、機種、站點、配置與收退料條件放在同一頁，適合盤點與跨資料核對。",
        placement: "bottom"
      },
      {
        id: "detailed-report-filters",
        route: "/search",
        query: { home_mode: "report" },
        target: "[data-tour='report-filter-panel']",
        title: "報表篩選：條件會依選擇順序聯動",
        description: "治具狀態預設已啟用，也可切換已停用或所有治具；其餘條件依選擇順序聯動並可組合使用。",
        placement: "bottom"
      },
      {
        id: "detailed-report-apply",
        route: "/search",
        query: { home_mode: "report" },
        target: "[data-tour='report-filter-actions']",
        title: "報表操作：重設、最大開站數與套用條件",
        description: "修改條件後按「套用條件」才更新表格與網址；最大開站結果可逐站點擊展開報表式治具明細。",
        placement: "top"
      },
      {
        id: "detailed-report-columns",
        route: "/search",
        query: { home_mode: "report" },
        target: "[data-tour='report-column-trigger']",
        title: "顯示欄位：保存偏好並自動隱藏空欄",
        description: "可使用三組欄位預設或逐欄勾選；整批篩選結果皆無資料的欄位會暫時隱藏，下一次有值時自動恢復。",
        placement: "bottom"
      },
      {
        id: "detailed-report-export",
        route: "/search",
        query: { home_mode: "report" },
        target: "[data-tour='report-export-trigger']",
        title: "報表匯出：輸出完整篩選結果",
        description: "選擇 XLSX 或 CSV 後，會匯出所有符合已套用條件的資料與目前實際顯示欄位，不受當前頁限制。",
        placement: "bottom"
      },
      {
        id: "detailed-report-results",
        route: "/search",
        query: { home_mode: "report" },
        target: "[data-tour='report-result-table']",
        title: "報表結果：圖片、配置狀態與收退料明細",
        description: "點治具代碼查看圖片；套用收／退料條件後可選擇展示日期、單號、datecode／編號、來源及數量明細。",
        placement: "top"
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
        description: "先選資料類型；治具查詢再選『治具資料』或『Datecode／序號』，然後輸入對應關鍵字：",
        bullets: [
          "治具資料：只依治具編號、名稱與儲位搜尋，不會被同名 Datecode／序號取代",
          "Datecode／序號：只依完整識別碼定位關聯治具與該識別碼紀錄",
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
        description: "治具、機種、站點切換核心主資料；Admin 可看到帳目管理與資料品質，Super Admin 另可管理客戶與使用者。",
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
        title: "治具資料品質分頁集中看主檔缺漏",
        description: "當主資料不完整時，改從這個分頁盤點儲位、最低水位、圖片與機種關聯缺漏。",
        placement: "bottom"
      },
      {
        id: "admin-quality-summary",
        route: "/master/quality",
        target: "[data-tour='master-quality-summary']",
        title: "先用上方摘要看異常分布，再決定優先順序",
        description: "摘要卡會把儲位／最低水位、圖片與機種關聯缺漏分開統計，方便決定先補哪一類。",
        placement: "bottom"
      },
      {
        id: "admin-quality-panel",
        route: "/master/quality",
        target: "[data-tour='master-quality-panel']",
        title: "從五個品質欄位直接開啟修正流程",
        description: "表格只保留治具編號、儲位、最低水位、機種關聯與圖片；缺漏項目可由對應欄位直接處理。",
        bullets: [
          "儲位與最低水位：直接在品質表格內補值並更新",
          "缺機種關聯：直接跳到產能管理的治具需求區補資料",
          "缺圖片：直接進入圖片維護流程"
        ],
        placement: "top"
      }
    ]
  },
  {
    id: "form-guest-quick-guide",
    sectionLabel: "Form UI 精簡版",
    label: "Form UI 唯讀快速上手",
    summary: "用 5 步認識固定表頭、功能列、庫存配置報表與收退料總檢視。",
    guestOnly: true,
    surface: "form",
    variant: "concise",
    steps: [
      {
        id: "form-guest-quick-heading",
        route: "/search",
        query: { ui_surface: "form", home_mode: "report" },
        target: "[data-tour='form-system-heading']",
        title: "Form UI 使用固定版頭",
        description: "版頭會顯示目前模組、客戶與登入身分；切換功能後位置不變，標題會跟著目前模組更新。",
        placement: "bottom"
      },
      {
        id: "form-guest-quick-workspaces",
        route: "/search",
        query: { ui_surface: "form", home_mode: "report" },
        target: "[data-tour='form-workspace-switcher']",
        title: "功能列切換訪客可用模組",
        description: "訪客可在篩選報表與收退料總檢視間切換；不會顯示可修改正式資料的功能。",
        placement: "bottom"
      },
      {
        id: "form-guest-quick-report-filters",
        route: "/search",
        query: { ui_surface: "form", home_mode: "report" },
        target: "[data-tour='report-filter-panel']",
        title: "先設定條件再套用",
        description: "可依治具、機種、站點、庫存水位與收退料條件縮小範圍；按套用條件後才更新結果。",
        placement: "bottom"
      },
      {
        id: "form-guest-quick-report-results",
        route: "/search",
        query: { ui_surface: "form", home_mode: "report" },
        target: "[data-tour='report-result-table']",
        title: "結果表可分頁、看圖片與匯出",
        description: "表格只載入目前頁；可調整每頁筆數、查看治具圖片，並匯出完整篩選結果。",
        placement: "top"
      },
      {
        id: "form-guest-quick-overview",
        route: "/inventory/overview",
        query: { ui_surface: "form" },
        target: "[data-tour='form-operation-results']",
        title: "收退料總檢視用來追歷史",
        description: "這裡依類型、日期、單號、治具、來源與操作人員查詢歷史，訪客只能查看與匯出。",
        placement: "top"
      }
    ]
  },
  {
    id: "form-guest-detailed-guide",
    sectionLabel: "Form UI 完整詳細版",
    label: "Form UI 訪客完整唯讀說明",
    summary: "逐區說明 Form UI 的版頭、客戶範圍、功能列、報表篩選、結果欄位與歷史總檢視。",
    guestOnly: true,
    surface: "form",
    variant: "detailed",
    steps: [
      {
        id: "form-guest-detail-heading",
        route: "/search",
        query: { ui_surface: "form", home_mode: "report" },
        target: "[data-tour='form-system-heading']",
        title: "版頭會清楚標示目前 Form 模組",
        description: "左側是目前模組與用途，中間是 Modern／Form 切換，右側整合新手教學、客戶、使用者與登出。",
        placement: "bottom"
      },
      {
        id: "form-guest-detail-customer",
        route: "/search",
        query: { ui_surface: "form", home_mode: "report" },
        target: "[data-tour='form-customer-scope']",
        title: "客戶選擇控制全部資料範圍",
        description: "前後按鈕可快速切換客戶，下拉可直接選擇；報表、歷史與匯出都會跟著更新。",
        placement: "bottom"
      },
      {
        id: "form-guest-detail-workspaces",
        route: "/search",
        query: { ui_surface: "form", home_mode: "report" },
        target: "[data-tour='form-workspace-switcher']",
        title: "功能列依權限分組",
        description: "日常作業、設定維護與系統管理分開排列；訪客只會看到篩選報表與唯讀總檢視。",
        placement: "bottom"
      },
      {
        id: "form-guest-detail-report-entry",
        route: "/search",
        query: { ui_surface: "form", home_mode: "report" },
        target: "[data-tour='form-workspace-report']",
        title: "篩選報表按鈕留在庫存配置報表",
        description: "按下後進入 /search 的 Form 報表頁；下一步會顯示到達頁的聯動篩選條件。",
        placement: "bottom"
      },
      {
        id: "form-guest-detail-report-filters",
        route: "/search",
        query: { ui_surface: "form", home_mode: "report" },
        target: "[data-tour='report-filter-panel']",
        title: "報表條件會聯動縮小選項",
        description: "先選的條件會限制後續選項；草稿與已套用條件分開，避免輸入到一半就改變結果。",
        placement: "bottom"
      },
      {
        id: "form-guest-detail-report-columns",
        route: "/search",
        query: { ui_surface: "form", home_mode: "report" },
        target: "[data-tour='report-column-trigger']",
        title: "欄位可依工作情境精簡",
        description: "可選現場庫存、配置檢查或完整報表，也能逐欄勾選；整批沒有資料的欄位會自動隱藏。",
        placement: "bottom"
      },
      {
        id: "form-guest-detail-report-results",
        route: "/search",
        query: { ui_surface: "form", home_mode: "report" },
        target: "[data-tour='report-result-table']",
        title: "大量結果採後端分頁",
        description: "每次只下載目前頁，表格使用頁面垂直捲動；匯出仍涵蓋全部符合篩選的資料。",
        placement: "top"
      },
      {
        id: "form-guest-detail-overview-entry",
        route: "/search",
        query: { ui_surface: "form", home_mode: "report" },
        target: "[data-tour='form-workspace-inventory-overview']",
        title: "收退料總檢視按鈕開啟唯讀歷史",
        description: "按下後進入 /inventory/overview；訪客可以查詢與匯出，但不會出現修改正式帳目的操作。",
        placement: "bottom"
      },
      {
        id: "form-guest-detail-overview-filters",
        route: "/inventory/overview",
        query: { ui_surface: "form" },
        target: "[data-tour='form-operation-filters']",
        title: "收退料總檢視提供完整查詢條件",
        description: "可查收／退料、來源、日期、治具、單號、datecode／編號與操作人員，套用後回到第 1 頁。",
        placement: "bottom"
      },
      {
        id: "form-guest-detail-overview-results",
        route: "/inventory/overview",
        query: { ui_surface: "form" },
        target: "[data-tour='form-operation-results']",
        title: "歷史結果可切換 50／100 筆",
        description: "上方顯示完整結果數，底部可翻頁；匯出使用相同篩選條件，不只輸出目前頁。",
        placement: "top"
      },
      {
        id: "form-guest-detail-onboarding-entry",
        route: "/search",
        query: { ui_surface: "form", home_mode: "report" },
        target: "[data-tour='form-onboarding-entry']",
        title: "Form UI 教學入口只顯示 Form 流程",
        description: "之後要重看時從版頭的 Form UI 教學進入；不會混入 Modern UI 的按鈕位置與操作說明。",
        placement: "bottom"
      }
    ]
  },
  {
    id: "form-quick-guide",
    sectionLabel: "Form UI 精簡版",
    label: "Form UI 日常作業快速上手",
    summary: "用 6 步走過報表、收退料匯入、總檢視、產能與資料維護。",
    requiresInventoryAccess: true,
    requiresMasterAccess: true,
    surface: "form",
    variant: "concise",
    steps: [
      {
        id: "form-quick-heading",
        route: "/search",
        query: { ui_surface: "form", home_mode: "report" },
        target: "[data-tour='form-system-heading']",
        title: "固定版頭顯示目前模組",
        description: "切換工作區後 H1 與用途會更新，但客戶、教學入口與帳號工具維持固定位置。",
        placement: "bottom"
      },
      {
        id: "form-quick-switcher",
        route: "/search",
        query: { ui_surface: "form", home_mode: "report" },
        target: "[data-tour='form-workspace-switcher']",
        title: "用功能列切換整個 Form 工作台",
        description: "日常作業、設定維護與系統管理都從這裡切換，不需要返回首頁找功能。",
        placement: "bottom"
      },
      {
        id: "form-quick-import",
        route: "/inventory",
        query: { ui_surface: "form" },
        target: "[data-tour='form-import-workspace']",
        title: "收退料匯入支援表格輸入與貼上",
        description: "先確認收／退料方向與來源，再輸入單號及明細；送出前可在同一張表檢查。",
        placement: "top",
        sandboxMode: true
      },
      {
        id: "form-quick-overview",
        route: "/inventory/overview",
        query: { ui_surface: "form" },
        target: "[data-tour='form-operation-results']",
        title: "總檢視集中追查收退料歷史",
        description: "使用上方條件查詢，結果支援 50／100 筆分頁與完整篩選匯出。",
        placement: "top"
      },
      {
        id: "form-quick-production",
        route: "/production/requirements",
        query: { ui_surface: "form" },
        target: "[data-tour='form-operation-results']",
        title: "產能維護包含需求與機種站點",
        description: "機種、站點與治具使用可搜尋 autocomplete；表格只載入目前頁，可直接新增或編輯列。",
        placement: "top"
      },
      {
        id: "form-quick-master",
        route: "/master/fixtures",
        query: { ui_surface: "form" },
        target: "[data-tour='form-operation-results']",
        title: "資料維護只載入目前主資料類型",
        description: "可切換治具、機種、站點；Super Admin 另可管理客戶與使用者，每頁可選 50／100 筆。",
        placement: "top"
      }
    ]
  },
  {
    id: "form-detailed-guide",
    sectionLabel: "Form UI 完整詳細版",
    label: "Form UI 全模組操作說明",
    summary: "逐一走過每個工作區按鈕與到達頁面，並詳細示範產能綁站點、綁治具及貼上匯入。",
    requiresInventoryAccess: true,
    requiresMasterAccess: true,
    surface: "form",
    variant: "detailed",
    steps: [
      {
        id: "form-detail-heading",
        route: "/search",
        query: { ui_surface: "form", home_mode: "report" },
        target: "[data-tour='form-system-heading']",
        title: "Form UI 版頭整合全域工具",
        description: "目前模組與用途在左側，介面切換在中間，右側依序是教學、客戶範圍、登入身分與登出。",
        placement: "bottom"
      },
      {
        id: "form-detail-customer",
        route: "/search",
        query: { ui_surface: "form", home_mode: "report" },
        target: "[data-tour='form-customer-scope']",
        title: "切換客戶會更新整個工作台",
        description: "報表、收退料、產能、主資料與圖片都受目前客戶限制；有未儲存列時系統會先要求確認。",
        placement: "bottom"
      },
      {
        id: "form-detail-switcher",
        route: "/search",
        query: { ui_surface: "form", home_mode: "report" },
        target: "[data-tour='form-workspace-switcher']",
        title: "工作區依工作性質分組",
        description: "日常作業包含報表、匯入與總檢視；設定維護包含產能、主資料與圖片；Admin 另有帳目與品質。",
        placement: "bottom"
      },
      {
        id: "form-detail-report-entry",
        route: "/search",
        query: { ui_surface: "form", home_mode: "report" },
        target: "[data-tour='form-workspace-report']",
        title: "篩選報表按鈕開啟庫存配置報表",
        description: "按下後進入 /search 的 Form 報表頁；下一步會直接顯示這個按鈕開啟後的條件區。",
        placement: "bottom"
      },
      {
        id: "form-detail-report-filters",
        route: "/search",
        query: { ui_surface: "form", home_mode: "report" },
        target: "[data-tour='report-filter-panel']",
        title: "先認識報表的聯動篩選方式",
        description: "關鍵字、治具狀態、治具、機種、站點、水位與儲位可組合；先選的條件會限制後續選項，避免選到不可能的組合。",
        bullets: [
          "關鍵字可查治具、機種、站點代碼或名稱",
          "治具狀態可切換啟用、停用或全部",
          "水位可只看低水位、缺料或正常",
          "儲位同時搜尋產線儲位與部門儲位"
        ],
        placement: "bottom"
      },
      {
        id: "form-detail-report-linked-fields",
        route: "/search",
        query: { ui_surface: "form", home_mode: "report" },
        target: "[data-tour='report-filter-fields']",
        title: "條件依選取順序互相縮小",
        description: "例如先選機種，站點與治具只保留該機種相關項目；已選順序會顯示成編號標籤，可單獨移除某一條件。",
        note: { tone: "info", text: "輸入中的草稿條件不會立即改變表格；必須按「套用條件」才正式查詢。" },
        placement: "bottom"
      },
      {
        id: "form-detail-report-transaction-filters",
        route: "/search",
        query: { ui_surface: "form", home_mode: "report" },
        target: "[data-tour='report-filter-fields']",
        title: "收退料條件可限定日期與來源",
        description: "可選今日收料、今日退料或指定日期區間，再選客供／自購來源；日期只在指定日期收／退料時生效。",
        bullets: [
          "今日模式不需要輸入起訖日期",
          "指定日期模式必須確認起始日不晚於結束日",
          "套用後結果可展開符合條件的交易明細"
        ],
        placement: "bottom"
      },
      {
        id: "form-detail-report-actions",
        route: "/search",
        query: { ui_surface: "form", home_mode: "report" },
        target: "[data-tour='report-filter-actions']",
        title: "重設、計算產能與套用條件",
        description: "「重設」清空條件；選定機種後可計算最大開站數；「套用條件」才更新 URL、筆數與結果表。",
        note: { tone: "info", text: "最大開站數取該機種與站點全部治具可支援站數的最小值。" },
        placement: "bottom"
      },
      {
        id: "form-detail-report-summary",
        route: "/search",
        query: { ui_surface: "form", home_mode: "report" },
        target: "[data-tour='report-result-toolbar']",
        title: "結果工具列先摘要目前資料",
        description: "工具列顯示總筆數、治具數、低水位／缺料、未配置、總庫存，以及客供與自購庫存；右側顯示目前頁範圍。",
        placement: "top"
      },
      {
        id: "form-detail-report-columns",
        route: "/search",
        query: { ui_surface: "form", home_mode: "report" },
        target: "[data-tour='report-column-trigger']",
        title: "顯示欄位可套用情境預設",
        description: "可選現場庫存、配置檢查或完整報表，也能逐欄勾選；整批沒有資料的欄位會暫時自動收合，選擇保存在瀏覽器。",
        placement: "bottom"
      },
      {
        id: "form-detail-report-results",
        route: "/search",
        query: { ui_surface: "form", home_mode: "report" },
        target: "[data-tour='report-result-table']",
        title: "逐列判讀庫存、配置與治具支援站數",
        description: "每列對應治具與配置關係；水位顯示正常、低水位或缺料，配置狀態標示是否缺機種／站點關聯。點治具代碼可開啟圖片預覽。",
        bullets: [
          "總庫存拆分為客供與自購數量",
          "需求數量是該機種站點每開一站所需數量",
          "此治具可支援站數是庫存除以需求數量後向下取整"
        ],
        placement: "top"
      },
      {
        id: "form-detail-report-export-pagination",
        route: "/search",
        query: { ui_surface: "form", home_mode: "report" },
        target: "[data-tour='report-result-toolbar']",
        title: "匯出與分頁不只處理畫面目前列",
        description: "可選 XLSX 或 CSV，匯出會取得全部符合篩選的資料；畫面則只載入目前頁，可在底部切換每頁筆數、上一頁、下一頁或跳至指定頁。",
        placement: "top"
      },
      {
        id: "form-detail-import-entry",
        route: "/search",
        query: { ui_surface: "form", home_mode: "report" },
        target: "[data-tour='form-workspace-import']",
        title: "收退料匯入按鈕開啟批次輸入頁",
        description: "按下後進入 /inventory；到達頁保留同一套 Form 版頭與工作區列，內容改成收退料共同欄位及明細表格。",
        placement: "bottom"
      },
      {
        id: "form-detail-import",
        route: "/inventory",
        query: { ui_surface: "form" },
        target: "[data-tour='form-import-workspace']",
        title: "到達收退料匯入後先看整張資料方格",
        description: "每列都包含收／退料、單號、治具、來源、datecode／編號、數量與備註。可以逐格輸入，也可以從 Excel 整塊貼到治具、編號、數量或備註欄開始填入。",
        placement: "top",
        sandboxMode: true
      },
      {
        id: "form-detail-import-mode-transaction",
        route: "/inventory",
        query: { ui_surface: "form" },
        target: "[data-tour='inventory-mode-column']",
        title: "先設定收／退料與必填單號",
        description: "收料會增加庫存，退料會扣除指定治具與編號的庫存；單號為必填。勾選「全部套用」可把第一個有效值套到所有列。",
        bullets: [
          "同一批可以混合收料與退料",
          "不同單號可放在不同列",
          "退料送出前會檢查目前可退庫存"
        ],
        placement: "top",
        sandboxMode: true
      },
      {
        id: "form-detail-import-fixture-ownership",
        route: "/inventory",
        query: { ui_surface: "form" },
        target: "[data-tour='inventory-fixture-column']",
        title: "選治具並確認客供或自購來源",
        description: "治具欄可輸入編號或名稱並對應既有治具；來源屬於每一筆交易，可選客供或自購，也能勾選全部套用。",
        note: { tone: "warning", text: "來源會影響客供／自購庫存拆分，送出前要確認每列正確。" },
        placement: "top",
        sandboxMode: true
      },
      {
        id: "form-detail-import-identifier-quantity",
        route: "/inventory",
        query: { ui_surface: "form" },
        target: "[data-tour='inventory-identifier-column']",
        title: "填入 datecode／編號與數量",
        description: "datecode／編號用來追蹤同一治具的細分庫存；數量必須是正整數。純數字 1–4 碼會依系統共同規則正規化，其餘值保留原文。",
        bullets: [
          "同一治具與編號的重複列，送出時會自動合併數量",
          "退料不可超過該治具與編號的可用庫存",
          "備註可逐列補充，不影響庫存計算"
        ],
        placement: "top",
        sandboxMode: true
      },
      {
        id: "form-detail-import-grid",
        route: "/inventory",
        query: { ui_surface: "form" },
        target: "[data-tour='inventory-paste-field']",
        title: "從 Excel 整塊貼上後自動解析",
        description: "可貼治具、datecode／編號、數量、備註四欄；也支援包含收／退料、單號與來源的完整七欄格式。貼上後會自動增加足夠列。",
        example: [
          { label: "四欄格式", value: "FIXTURE-001<TAB>2608<TAB>5<TAB>首批入庫" },
          { label: "完整格式", value: "receipt<TAB>TX-001<TAB>FIXTURE-001<TAB>2608<TAB>5<TAB>customer_supplied<TAB>首批入庫" }
        ],
        placement: "top",
        sandboxMode: true
      },
      {
        id: "form-detail-import-preview",
        route: "/inventory",
        query: { ui_surface: "form" },
        target: "[data-tour='inventory-ready-summary']",
        title: "預覽會分類正常、待確認與錯誤列",
        description: "精確匹配的列可直接送出；相似治具要確認是否同一治具，找不到的治具可新增或略過，格式錯誤則要回原始表格修正。",
        bullets: [
          "正常列可展開查看目前庫存與交易後庫存",
          "例外區預設只展開前 3 筆",
          "略過的列不會包含在 API 請求中"
        ],
        placement: "top",
        sandboxMode: true
      },
      {
        id: "form-detail-import-actions",
        route: "/inventory",
        query: { ui_surface: "form" },
        target: "[data-tour='detailed-inventory-actions']",
        title: "清空、匯出檢查結果或正式送出",
        description: "「清空」移除草稿，「匯出篩選結果」下載目前解析清單；只有所有列都已處理、單號齊全且庫存檢查通過時才能送出。",
        note: { tone: "warning", text: "目前是教學試跑模式，按送出只模擬流程，不會寫入正式收退料資料。" },
        placement: "top",
        sandboxMode: true
      },
      {
        id: "form-detail-overview-entry",
        route: "/inventory",
        query: { ui_surface: "form" },
        target: "[data-tour='form-workspace-inventory-overview']",
        title: "收退料總檢視按鈕開啟歷史明細",
        description: "按下後進入 /inventory/overview；下一步顯示到達頁的完整查詢條件。",
        placement: "bottom",
        sandboxMode: true
      },
      {
        id: "form-detail-overview-filters",
        route: "/inventory/overview",
        query: { ui_surface: "form" },
        target: "[data-tour='form-operation-filters']",
        title: "總檢視可追查單號與操作人員",
        description: "除了類型與日期，也可查來源、治具、單號、datecode／編號與操作人員；重新整理保留條件。",
        placement: "bottom"
      },
      {
        id: "form-detail-overview-results",
        route: "/inventory/overview",
        query: { ui_surface: "form" },
        target: "[data-tour='form-operation-results']",
        title: "總檢視採後端分頁",
        description: "每頁 50／100 筆，只渲染目前頁；底部翻頁，上方匯出完整篩選結果。",
        placement: "top"
      },
      {
        id: "form-detail-production-entry",
        route: "/inventory/overview",
        query: { ui_surface: "form" },
        target: "[data-tour='form-workspace-production']",
        title: "產能按鈕開啟配置維護",
        description: "按下後進入 /production/requirements；產能分為「治具需求」與「機種站點」兩張資料表。",
        placement: "bottom"
      },
      {
        id: "form-detail-production-filters",
        route: "/production/requirements",
        query: { ui_surface: "form" },
        target: "[data-tour='form-operation-filters']",
        title: "到達產能頁後先理解兩張資料表",
        description: "「機種站點」先定義某機種可使用哪些站點；「治具需求」再定義該機種在該站點每開一站需要哪些治具與數量。機種與站點篩選使用後端 autocomplete。",
        placement: "bottom"
      },
      {
        id: "form-detail-production-view-selector",
        route: "/production/requirements",
        query: { ui_surface: "form" },
        target: "[data-tour='form-production-view-selector']",
        title: "資料表下拉切換綁定層級",
        description: "建議順序是先選「機種站點」完成站點綁定，再選「治具需求」綁定治具；URL 會分別變成 /production/mapping 與 /production/requirements。",
        bullets: [
          "機種站點：一列代表一個 model + station 關係",
          "治具需求：一列代表 model + station + fixture + required_qty"
        ],
        placement: "bottom"
      },
      {
        id: "form-detail-production-requirement-add",
        route: "/production/requirements",
        query: { ui_surface: "form" },
        target: "[data-tour='form-production-add-row']",
        title: "新增一列綁定站點所需治具",
        description: "按下後表格頂端出現輸入列。依序選機種、站點、治具，再輸入每開一站需要的數量並儲存。",
        bullets: [
          "輸入代碼或名稱後，從 autocomplete 建議中選取正式資料",
          "每站需求必須大於 0",
          "同一機種、站點、治具不可重複建立"
        ],
        placement: "bottom"
      },
      {
        id: "form-detail-production-requirement-table",
        route: "/production/requirements",
        query: { ui_surface: "form" },
        target: "[data-tour='form-production-requirements-table']",
        title: "治具需求表顯示綁定結果與產能",
        description: "儲存後每列顯示機種、站點、治具、每站需求、目前庫存與此治具可支援站數；支援站數是目前庫存除以每站需求後向下取整。",
        note: { tone: "info", text: "完整站點產能仍以該 model + station 所有治具支援站數的最小值為準。" },
        placement: "top"
      },
      {
        id: "form-detail-production-requirement-paste",
        route: "/production/requirements",
        query: { ui_surface: "form" },
        target: "[data-tour='form-production-paste-import']",
        title: "治具需求也可從 Excel 貼上匯入",
        description: "按「貼上匯入」後貼四欄：機種編號、站點編號、治具編號、每站需求量。先按「檢查差異」，系統會把原需求量與匯入需求量並列預覽；相同資料略過，新綁定新增，數量不同時必須再確認「直接取代」才會更新。",
        note: { tone: "warning", text: "取代只更新貼上內容中的差異列，不會刪除未貼上的其他站點或治具綁定。" },
        example: [{ label: "四欄格式", value: "MODEL-A<TAB>STATION-01<TAB>FIXTURE-001<TAB>2" }],
        placement: "bottom"
      },
      {
        id: "form-detail-production-mapping-view",
        route: "/production/mapping",
        query: { ui_surface: "form" },
        target: "[data-tour='form-production-view-selector']",
        title: "切到機種站點頁先建立站點綁定",
        description: "到達 /production/mapping 後，資料表下拉顯示「機種站點」；這一步只建立機種與站點的關係，還不指定治具。",
        placement: "bottom"
      },
      {
        id: "form-detail-production-mapping-add",
        route: "/production/mapping",
        query: { ui_surface: "form" },
        target: "[data-tour='form-production-add-row']",
        title: "新增一列把站點綁到機種",
        description: "按下後在輸入列選擇機種與站點，再按儲存。完成後該站點才能作為這個機種的配置關係被查詢與維護。",
        bullets: [
          "機種與站點必須先存在於主資料",
          "可輸入代碼或名稱搜尋",
          "已存在的相同綁定不可重複新增"
        ],
        placement: "bottom"
      },
      {
        id: "form-detail-production-mapping-table",
        route: "/production/mapping",
        query: { ui_surface: "form" },
        target: "[data-tour='form-production-mappings-table']",
        title: "機種站點表顯示所有已綁定站點",
        description: "每列是一組機種與站點；可以編輯、更換或刪除。刪除前要確認相關治具需求是否仍需保留。",
        placement: "top"
      },
      {
        id: "form-detail-production-mapping-paste",
        route: "/production/mapping",
        query: { ui_surface: "form" },
        target: "[data-tour='form-production-paste-import']",
        title: "機種站點支援兩欄貼上匯入",
        description: "按「貼上匯入」後貼兩欄：機種編號、站點編號。先按「檢查差異」預覽哪些是新綁定、哪些已存在；相同綁定會略過，新站點關係才會新增。因同一機種可合法綁多個站點，不會把不同站點誤判成取代。",
        example: [{ label: "兩欄格式", value: "MODEL-A<TAB>STATION-01" }],
        placement: "bottom"
      },
      {
        id: "form-detail-master-entry",
        route: "/production/mapping",
        query: { ui_surface: "form" },
        target: "[data-tour='form-workspace-master']",
        title: "資料維護按鈕開啟主資料頁",
        description: "按下後進入 /master/fixtures；可切換治具、機種、站點，Super Admin 另可維護客戶與使用者。",
        placement: "bottom"
      },
      {
        id: "form-detail-master-filters",
        route: "/master/fixtures",
        query: { ui_surface: "form" },
        target: "[data-tour='form-operation-filters']",
        title: "資料表下拉決定目前維護的主資料",
        description: "治具、機種、站點、客戶與使用者各自查詢，不會一次下載全部資料集；每種資料表都有獨立 URL，可直接加入書籤。",
        bullets: [
          "治具：/master/fixtures",
          "機種：/master/models",
          "站點：/master/stations",
          "客戶與使用者：只對 Super Admin 顯示"
        ],
        placement: "bottom"
      },
      {
        id: "form-detail-master-toolbar",
        route: "/master/fixtures",
        query: { ui_surface: "form" },
        target: "[data-tour='form-master-toolbar']",
        title: "資料維護工具列負責匯出、新增與分頁",
        description: "匯出會收集完整篩選結果；新增一列會在表格頂端開啟輸入列；每頁可切換 50／100 筆。",
        placement: "top"
      },
      {
        id: "form-detail-master-fixtures",
        route: "/master/fixtures",
        query: { ui_surface: "form" },
        target: "[data-tour='form-master-fixture-table']",
        title: "治具主資料包含儲位與最低水位",
        description: "新增或編輯時維護治具編號、名稱、產線儲位、部門儲位、最低水位與啟用狀態；報表水位與儲位顯示都來自這裡。",
        bullets: [
          "治具編號在目前客戶內不可重複",
          "最低水位不可小於 0",
          "永久刪除前會提示是否保留交易歷史快照"
        ],
        placement: "top"
      },
      {
        id: "form-detail-master-models",
        route: "/master/models",
        query: { ui_surface: "form" },
        target: "[data-tour='form-master-model-table']",
        title: "機種主資料先建立代碼與名稱",
        description: "新增機種後，再到產能的機種站點頁綁定站點，接著到治具需求頁綁治具。編輯代碼或停用時要確認既有產能配置仍符合現場。",
        placement: "top"
      },
      {
        id: "form-detail-master-stations",
        route: "/master/stations",
        query: { ui_surface: "form" },
        target: "[data-tour='form-master-station-table']",
        title: "站點主資料可被多個機種共用",
        description: "站點只定義代碼、名稱與狀態；它屬於哪些機種、需要哪些治具，要到產能頁以 model + station 維護，不能只靠 station 推斷機種。",
        note: { tone: "info", text: "同一站點可被多個機種使用，但治具需求仍是機種專屬。" },
        placement: "top"
      },
      {
        id: "form-detail-master-customers",
        route: "/master/customers",
        query: { ui_surface: "form" },
        target: "[data-tour='form-master-customer-table']",
        title: "Super Admin 可維護客戶代碼與名稱",
        description: "客戶是治具、機種、站點、庫存與權限的資料範圍。新增後還需要在使用者資料表把客戶授權給帳號，帳號才看得到。",
        placement: "top",
        requiresSuperAdminAccess: true
      },
      {
        id: "form-detail-master-users",
        route: "/master/users",
        query: { ui_surface: "form" },
        target: "[data-tour='form-master-user-table']",
        title: "Super Admin 可維護使用者身分與客戶範圍",
        description: "新增使用者需填帳號、顯示名稱、角色、初始密碼與至少一個可存取客戶；編輯時可調整 Email、角色、啟用狀態與全部客戶勾選。",
        bullets: [
          "super_admin、admin 與 user 都只限已授權客戶",
          "guest 可查看全部客戶但唯讀",
          "列表會顯示每位使用者目前授權的客戶"
        ],
        placement: "top",
        requiresSuperAdminAccess: true
      },
      {
        id: "form-detail-master-user-scope",
        route: "/master/users",
        query: { ui_surface: "form" },
        target: "[data-tour='form-operation-results']",
        title: "編輯使用者時再展開客戶多選面板",
        description: "按新增一列或既有帳號的編輯後，可依代碼／名稱搜尋、逐筆勾選、全選搜尋結果、點標籤移除或清除全部；至少保留一個客戶才能儲存。",
        placement: "top",
        requiresSuperAdminAccess: true
      },
      {
        id: "form-detail-master-results",
        route: "/master/fixtures",
        query: { ui_surface: "form" },
        target: "[data-tour='form-operation-results']",
        title: "新增、編輯與刪除都在目前表格完成",
        description: "輸入列提供儲存與取消；既有列提供編輯，治具、機種與站點另有永久刪除。切換客戶、工作區或介面前若尚未儲存，系統會提示是否放棄。",
        placement: "top"
      },
      {
        id: "form-detail-image-entry",
        route: "/master/fixtures",
        query: { ui_surface: "form" },
        target: "[data-tour='form-workspace-image']",
        title: "圖片維護按鈕開啟圖片清單",
        description: "按下後進入 /master/images；下一步顯示圖片維護的搜尋條件與分頁清單。",
        placement: "bottom"
      },
      {
        id: "form-detail-image-filters",
        route: "/master/images",
        query: { ui_surface: "form" },
        target: "[data-tour='form-image-filters']",
        title: "圖片維護可依編號、名稱與圖片狀態搜尋",
        description: "圖片狀態直接依檔案目錄判定；可切換已有圖片或尚無圖片，結果使用 50／100 筆後端分頁。",
        placement: "bottom"
      },
      {
        id: "form-detail-image-results",
        route: "/master/images",
        query: { ui_surface: "form" },
        target: "[data-tour='form-image-results']",
        title: "圖片可預覽、單張替換或批次上傳",
        description: "批次檔名需使用治具編號；單次最多 50 張、每張小於 5 MB。匯出會收集全部篩選頁面。",
        placement: "top"
      },
      {
        id: "form-detail-ledger-entry",
        route: "/master/images",
        query: { ui_surface: "form" },
        target: "[data-tour='form-workspace-ledger']",
        title: "收退料帳目管理按鈕開啟案件管理",
        description: "Admin 按下後進入 /master/ledger；可查詢案件、查看明細、重算庫存或依規則撤回交易。",
        placement: "bottom",
        requiresAdminAccess: true
      },
      {
        id: "form-detail-ledger-page",
        route: "/master/ledger",
        query: { ui_surface: "form" },
        target: "[data-tour='form-admin-results']",
        title: "到達帳目管理頁後先選案件再操作",
        description: "左側是分頁案件清單，右側是選取案件的明細與管理操作；重算與撤回都會使用系統確認流程。",
        placement: "top",
        requiresAdminAccess: true
      },
      {
        id: "form-detail-quality-entry",
        route: "/master/ledger",
        query: { ui_surface: "form" },
        target: "[data-tour='form-workspace-quality']",
        title: "治具資料品質按鈕開啟缺漏檢查",
        description: "Admin 按下後進入 /master/quality；可依問題類型查看缺儲位／最低水位、缺圖片或缺機種關聯。",
        placement: "bottom",
        requiresAdminAccess: true
      },
      {
        id: "form-detail-quality-page",
        route: "/master/quality",
        query: { ui_surface: "form" },
        target: "[data-tour='form-admin-results']",
        title: "到達資料品質頁後直接處理問題",
        description: "五欄品質表會提供儲位／最低水位就地修正，或導向產能與圖片維護；完成後重新整理確認異常已消失。",
        placement: "top",
        requiresAdminAccess: true
      },
      {
        id: "form-detail-replay",
        route: "/search",
        query: { ui_surface: "form", home_mode: "report" },
        target: "[data-tour='form-onboarding-entry']",
        title: "從 Form UI 入口重播 Form 教學",
        description: "精簡版適合快速複習，完整詳細版適合逐模組查閱；Modern UI 有自己的獨立教學入口與流程。",
        placement: "bottom"
      }
    ]
  },
  {
    id: "workbench-guest-quick-guide",
    sectionLabel: "工作台 UI 訪客精簡版",
    label: "查詢與唯讀管理",
    summary: "快速認識工作台三欄查詢、結果明細與訪客可用的總檢視。",
    guestOnly: true,
    surface: "workbench",
    variant: "concise",
    steps: [
      {
        id: "workbench-guest-entry",
        route: "/search",
        query: { ui_surface: "workbench", workbench_mode: "fixture" },
        target: "[data-tour='workbench-onboarding-entry']",
        title: "頂欄隨時可重開工作台教學",
        description: "這份教學只說明工作台 UI；切換 Modern UI 或 Form UI 後會看到各自的教學內容。",
        placement: "bottom"
      },
      {
        id: "workbench-guest-modes",
        route: "/search",
        query: { ui_surface: "workbench", workbench_mode: "fixture" },
        target: "[data-tour='workbench-mode-tabs']",
        title: "四個工作台分頁集中在左欄",
        description: "訪客可以唯讀查詢治具／機種，也能從管理後臺分頁進入收退料總檢視與角色可用的匯出中心；收退料操作仍會依權限停用。",
        placement: "bottom"
      },
      {
        id: "workbench-guest-results",
        route: "/search",
        query: { ui_surface: "workbench", workbench_mode: "fixture" },
        target: "[data-tour='workbench-results']",
        title: "中間看結果，右側看選取明細",
        description: "先在左側輸入條件，中間列表用來比較結果，右側會集中顯示圖片、儲位與關聯資料。",
        placement: "left"
      }
    ]
  },
  {
    id: "workbench-guest-detailed-guide",
    sectionLabel: "工作台 UI 訪客完整教學",
    label: "完整唯讀工作台導覽",
    summary: "從三欄工作台一路看到管理後臺的收退料總檢視。",
    guestOnly: true,
    surface: "workbench",
    variant: "detailed",
    steps: [
      {
        id: "workbench-guest-detail-entry",
        route: "/search",
        query: { ui_surface: "workbench", workbench_mode: "fixture" },
        target: "[data-tour='workbench-onboarding-entry']",
        title: "工作台 UI 有獨立教學",
        description: "教學目標會跟隨工作台的實際三欄版面，不會跳回 Modern UI。",
        placement: "bottom"
      },
      {
        id: "workbench-guest-detail-modes",
        route: "/search",
        query: { ui_surface: "workbench", workbench_mode: "fixture" },
        target: "[data-tour='workbench-mode-tabs']",
        title: "左欄先選工作模式",
        description: "治具查詢適合盤點庫存與儲位；機種查詢適合查看站點、治具需求與瓶頸；管理後臺分頁集中唯讀入口與匯出中心。",
        placement: "bottom"
      },
      {
        id: "workbench-guest-detail-query",
        route: "/search",
        query: { ui_surface: "workbench", workbench_mode: "fixture", fixture_search: "fixture" },
        target: "[data-tour='workbench-query-form']",
        title: "先選治具資料或 Datecode／序號",
        description: "治具資料可用完整或部分編號、名稱與儲位；要查識別碼時切到 Datecode／序號，兩種搜尋互不干擾。查無結果可直接清除再重試。",
        placement: "right"
      },
      {
        id: "workbench-guest-detail-result",
        route: "/search",
        query: { ui_surface: "workbench", workbench_mode: "fixture" },
        target: "[data-tour='workbench-results']",
        title: "結果與明細分欄閱讀",
        description: "中間欄保留可掃讀列表，右欄顯示目前選取項目的完整資訊。",
        placement: "left"
      },
      {
        id: "workbench-guest-detail-management",
        route: "/search",
        query: { ui_surface: "workbench", workbench_mode: "management" },
        target: "[data-tour='workbench-management-launcher']",
        title: "管理入口集中在快速作業分頁",
        description: "訪客可進入收退料總檢視與角色可用的匯出中心；不可操作的產能與主資料入口不會顯示。",
        placement: "right"
      }
    ]
  },
  {
    id: "workbench-quick-guide",
    sectionLabel: "工作台 UI 精簡版",
    label: "現場收退料與查詢",
    summary: "快速走過模式切換、單筆作業、批次作業與三欄查詢。",
    requiresInventoryAccess: true,
    surface: "workbench",
    variant: "concise",
    steps: [
      {
        id: "workbench-quick-entry",
        route: "/search",
        query: { ui_surface: "workbench", workbench_mode: "transaction", transaction_type: "receipt" },
        target: "[data-tour='workbench-onboarding-entry']",
        title: "從頂欄開啟工作台教學",
        description: "可在任何工作台頁面重播，不會切換到其他 UI。",
        placement: "bottom"
      },
      {
        id: "workbench-quick-modes",
        route: "/search",
        query: { ui_surface: "workbench", workbench_mode: "transaction", transaction_type: "receipt" },
        target: "[data-tour='workbench-mode-tabs']",
        title: "四個工作區集中在左欄",
        description: "收料與退料合併成單一作業面板，另有治具查詢、機種查詢與管理後臺快捷入口。",
        placement: "bottom"
      },
      {
        id: "workbench-quick-form",
        route: "/search",
        query: { ui_surface: "workbench", workbench_mode: "transaction", transaction_type: "receipt" },
        target: "[data-tour='workbench-transaction-form']",
        title: "單筆收退料先確認單號與治具",
        description: "送出前確認 datecode／流水號、數量與來源；批次按鈕會在中間欄展開。",
        placement: "right"
      },
      {
        id: "workbench-quick-results",
        route: "/search",
        query: { ui_surface: "workbench", workbench_mode: "fixture" },
        target: "[data-tour='workbench-results']",
        title: "中間結果、右側明細",
        description: "列表與圖片／儲位／關聯分欄，讓現場人員不必離開工作台。",
        placement: "left"
      }
    ]
  },
  {
    id: "workbench-detailed-guide",
    sectionLabel: "工作台 UI 完整教學",
    label: "完整工作台與管理後臺導覽",
    summary: "涵蓋單筆／批次收退料、治具與機種查詢，以及管理模組入口。",
    requiresInventoryAccess: true,
    surface: "workbench",
    variant: "detailed",
    steps: [
      {
        id: "workbench-detail-entry",
        route: "/search",
        query: { ui_surface: "workbench", workbench_mode: "transaction", transaction_type: "receipt" },
        target: "[data-tour='workbench-onboarding-entry']",
        title: "工作台教學固定在頂欄",
        description: "PC、Notebook 與 Tablet 都能從這裡開始或重播工作台專屬流程。",
        placement: "bottom"
      },
      {
        id: "workbench-detail-modes",
        route: "/search",
        query: { ui_surface: "workbench", workbench_mode: "transaction", transaction_type: "receipt" },
        target: "[data-tour='workbench-mode-tabs']",
        title: "先選作業模式",
        description: "收退料共用一張表單；治具與機種切換時會依目前結果提示可查詢的關聯項目；管理後臺則集中所有角色可用入口。",
        placement: "bottom"
      },
      {
        id: "workbench-detail-transaction",
        route: "/search",
        query: { ui_surface: "workbench", workbench_mode: "transaction", transaction_type: "receipt" },
        target: "[data-tour='workbench-transaction-form']",
        title: "單筆收退料在左欄完成",
        description: "依序輸入單號、治具、識別碼、數量、來源與備註；送出後近期紀錄會更新。",
        note: { tone: "warning", text: "送出會改變庫存；正式操作前請再次確認模式、治具與數量。" },
        placement: "right"
      },
      {
        id: "workbench-detail-batch",
        route: "/search",
        query: { ui_surface: "workbench", workbench_mode: "transaction", transaction_type: "receipt", workbench_batch: "true" },
        target: "[data-tour='workbench-batch-panel']",
        title: "批次收料與退料合併在中間欄",
        description: "同一批次可逐列選擇收料或退料，版面尺寸會配合工作台中欄，不使用 Form UI 視窗。",
        placement: "left"
      },
      {
        id: "workbench-detail-query",
        route: "/search",
        query: { ui_surface: "workbench", workbench_mode: "fixture", fixture_search: "fixture" },
        target: "[data-tour='workbench-query-form']",
        title: "治具資料與識別碼分開搜尋",
        description: "治具分頁先選『治具資料』或『Datecode／序號』，避免同文字互相覆蓋；機種分頁維持代碼／名稱搜尋。左欄輸入，中間選結果，右欄看明細。",
        placement: "right"
      },
      {
        id: "workbench-detail-management",
        route: "/search",
        query: { ui_surface: "workbench", workbench_mode: "management" },
        target: "[data-tour='workbench-management-launcher']",
        title: "管理後臺入口集中在快速作業",
        description: "收退料總檢視、產能設定、資料維護、Admin 帳目／品質與匯出中心都從這裡進入，並依角色隱藏不可用項目。",
        placement: "right"
      },
      {
        id: "workbench-detail-filters",
        route: "/inventory/overview",
        query: { ui_surface: "workbench" },
        target: "[data-tour='form-operation-filters']",
        title: "可組合的條件使用複選",
        description: "類型、來源與狀態等可同時成立的條件可勾選多項；資料表、排序與格式等互斥設定仍維持單選。",
        placement: "bottom"
      },
      {
        id: "workbench-detail-ledger",
        route: "/master/ledger",
        query: { ui_surface: "workbench" },
        target: "[data-tour='workbench-admin-results']",
        title: "帳目管理使用工作台案件雙欄",
        description: "左側選擇收退料案件，右側核對明細、重算或撤回；篩選與匯出都保留在工作台中欄。",
        placement: "top",
        requiresAdminAccess: true
      },
      {
        id: "workbench-detail-quality",
        route: "/master/quality",
        query: { ui_surface: "workbench" },
        target: "[data-tour='workbench-admin-results']",
        title: "品質問題以工作台指標與修正表呈現",
        description: "先看五項異常指標，再依問題複選縮小資料；可就地補儲位／水位或導向圖片、產能與帳目處理。",
        placement: "top",
        requiresAdminAccess: true
      }
    ]
  },
  {
    id: "form-admin-user-access",
    sectionLabel: "Form UI Super Admin 精簡版",
    label: "使用者可存取客戶多選",
    summary: "專門說明如何搜尋、全選、清除並勾選多個客戶後儲存使用者權限。",
    requiresMasterAccess: true,
    requiresSuperAdminAccess: true,
    surface: "form",
    variant: "concise",
    steps: [
      {
        id: "form-admin-users-filter",
        route: "/master/users",
        query: { ui_surface: "form" },
        target: "[data-tour='form-operation-filters']",
        title: "先進入資料維護的使用者清單",
        description: "可依帳號、姓名或 Email 搜尋；按新增一列或既有使用者的編輯，才會顯示權限多選面板。",
        placement: "bottom"
      },
      {
        id: "form-admin-user-scope",
        route: "/master/users",
        query: { ui_surface: "form" },
        target: "[data-tour='form-operation-results']",
        title: "新增或編輯後展開可存取客戶",
        description: "面板會顯示已選數量與客戶清單；可搜尋代碼／名稱、逐筆勾選、全選目前搜尋結果或清除全部。",
        note: { tone: "info", text: "至少必須保留一個客戶；未選任何客戶時不會送出 API。" },
        placement: "top"
      },
      {
        id: "form-admin-user-scope-save",
        route: "/master/users",
        query: { ui_surface: "form" },
        target: "[data-tour='form-operation-results']",
        title: "確認已選客戶後儲存",
        description: "列表會以客戶代碼與名稱顯示授權範圍；再次編輯時會回填所有既有勾選，可繼續新增或取消。",
        placement: "top"
      }
    ]
  }
];

export const onboardingFlowMap = new Map(onboardingFlows.map((flow) => [flow.id, flow]));

export function onboardingSurfaceForFlow(flow: OnboardingFlow): OnboardingSurface {
  return flow.surface ?? "modern";
}

export function onboardingVariantForFlow(flow: OnboardingFlow): OnboardingVariant {
  if (flow.variant) {
    return flow.variant;
  }
  return flow.id === "guest-readonly-guide" || flow.id === "system-detailed-guide"
    ? "detailed"
    : "concise";
}

export function getOnboardingFlow(flowId: OnboardingFlowId | null): OnboardingFlow | null {
  if (!flowId) {
    return null;
  }
  return onboardingFlowMap.get(flowId) ?? null;
}
