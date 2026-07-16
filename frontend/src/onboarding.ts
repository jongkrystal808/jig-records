export type TourPlacement = "top" | "bottom" | "left" | "right";

export type OnboardingFlowId =
  | "search-basics"
  | "inventory-batch"
  | "inventory-overview"
  | "master-basics"
  | "production-mapping"
  | "production-requirements";

export interface OnboardingStep {
  id: string;
  route: string;
  target: string;
  title: string;
  description: string;
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
  steps: OnboardingStep[];
}

export const onboardingFlows: OnboardingFlow[] = [
  {
    id: "search-basics",
    sectionLabel: "首頁查詢",
    label: "查詢工作台",
    summary: "從首頁查詢、切換區塊，到重播教學入口的基本操作。",
    steps: [
      {
        id: "search-onboarding-entry",
        route: "/search",
        target: "[data-tour='search-onboarding-entry']",
        title: "右下角固定保留教學入口",
        description: "要看教學時，從這個入口打開教學選單即可。之後若要重看其他教學分類，也從這裡重新開啟。",
        placement: "bottom"
      },
      {
        id: "search-mode",
        route: "/search",
        target: "[data-tour='search-mode-switch']",
        title: "先決定查治具還是查機種",
        description: "治具模式適合追庫存、圖片、收退料與站點需求；機種模式適合追站點配置、治具需求與產能分析。先選模式，再輸入關鍵字。",
        placement: "bottom"
      },
      {
        id: "search-input",
        route: "/search",
        target: "[data-tour='search-query-field']",
        title: "查詢欄支援代碼與名稱",
        description: "可直接輸入治具編號、治具名稱、機種代碼或機種名稱。先查到主體，再決定要看圖片、歷史收退料或站點需求。",
        placement: "bottom"
      },
      {
        id: "search-sections",
        route: "/search",
        target: "[data-tour='search-section-chips']",
        title: "查到資料後，用區塊籤控制畫面內容",
        description: "這裡可以切換總覽、圖片、datecode/編號庫存、收退料、相關機種、站點詳細或資料維護。新手不需要一次看全部，先開自己要的區塊即可。",
        placement: "bottom"
      }
    ]
  },
  {
    id: "inventory-batch",
    sectionLabel: "收退料",
    label: "批次收 / 退料",
    summary: "說明批次貼上格式、未知治具處理、解析預覽與正式送出流程。",
    requiresInventoryAccess: true,
    steps: [
      {
        id: "inventory-entry",
        route: "/search",
        target: "[data-tour='inventory-entry-trigger']",
        title: "收退料從這個全域入口開啟",
        description: "不需要先切頁。從首頁頂部直接打開收 / 退料視窗，就能在任何頁面快速處理批次資料。",
        placement: "bottom"
      },
      {
        id: "inventory-mode",
        route: "/search",
        target: "[data-tour='inventory-batch-panel'] [data-tour='inventory-mode-switch']",
        title: "先切換收料或退料模式",
        description: "貼資料前先確認方向。收料會把數量加回庫存，退料會把數量扣回去；單號與備註也會一起記錄到交易歷史。",
        placement: "bottom",
        openBatchModal: true
      },
      {
        id: "inventory-batch-panel",
        route: "/search",
        target: "[data-tour='inventory-batch-panel']",
        title: "整個批次操作都在這個面板完成",
        description: "上方填單號與備註，中間貼批次內容，下方看解析結果與異常處理。送出前不需要切去別頁確認。",
        placement: "right",
        openBatchModal: true
      },
      {
        id: "inventory-paste-format",
        route: "/search",
        target: "[data-tour='inventory-batch-panel'] [data-tour='inventory-paste-field']",
        title: "批次貼上支援兩種格式",
        description: "可貼兩行一組：第一行 `治具代碼-datecode/編號`，第二行 `數量`；也可貼單行表格式：`治具代碼[TAB]datecode/編號[TAB]數量`。這個欄位可直接按 Tab 輸入分隔。若 datecode/編號是 1 到 4 碼純數字，系統會自動左補零成 4 碼；其餘值會按原樣保留。",
        placement: "left",
        openBatchModal: true
      },
      {
        id: "inventory-preview",
        route: "/search",
        target: "[data-tour='inventory-batch-panel'] [data-tour='inventory-preview-table']",
        title: "貼上後先看解析預覽，不要直接送出",
        description: "系統會把每一列拆成治具、datecode/編號、數量與狀態。只有 `ready` 的列會真的送出；`error` 代表原始格式需要先修正。",
        placement: "top",
        openBatchModal: true
      },
      {
        id: "inventory-missing-fixture",
        route: "/search",
        target: "[data-tour='inventory-batch-panel'] [data-tour='inventory-preview-table']",
        title: "收料遇到沒建過的治具，要先決定怎麼處理",
        description: "如果系統找到相近代碼，會先標成 `needs-confirm`，你可以按 `同一治具` 採用既有治具，或改為新增。若完全找不到，會標成 `needs-add`，可按 `新增治具` 現場建立，或先 `略過` 這一列。",
        placement: "top",
        openBatchModal: true
      },
      {
        id: "inventory-submit",
        route: "/search",
        target: "[data-tour='inventory-batch-panel'] [data-tour='inventory-submit-action']",
        title: "確認單號與待處理列都清乾淨後再送出",
        description: "畫面上只要還有 `needs-confirm`、`needs-add` 或 `error`，系統就不會放行。先把異常列處理完，再按送出收料或送出退料寫入正式記錄。",
        placement: "top",
        openBatchModal: true
      }
    ]
  },
  {
    id: "inventory-overview",
    sectionLabel: "收退料",
    label: "收退料總檢視",
    summary: "從首頁入口到總檢視篩選條件，專看歷史收退料紀錄。",
    steps: [
      {
        id: "overview-menu",
        route: "/search",
        target: "[data-tour='home-more-menu-trigger']",
        title: "總檢視入口收在更多功能",
        description: "若不是立即做收退料，而是要查歷史記錄、單號或 datecode/編號，就先從首頁打開更多功能。",
        placement: "bottom",
        openMoreMenu: true
      },
      {
        id: "overview-entry",
        route: "/search",
        target: "[data-tour='home-overview-entry']",
        title: "從這裡進入收退料總檢視",
        description: "這個入口會帶你到專門查歷史收退料的頁面，適合查某個治具、某段日期或某張單號的過往異動。",
        placement: "left",
        openMoreMenu: true
      },
      {
        id: "overview-page",
        route: "/inventory/overview",
        target: "[data-tour='overview-page-head']",
        title: "總檢視頁面集中看全部歷史記錄",
        description: "進來後先確認目前客戶與查詢範圍。這裡的列表不是單一治具畫面，而是整個客戶底下的收退料總表。",
        placement: "bottom"
      },
      {
        id: "overview-filters",
        route: "/inventory/overview",
        target: "[data-tour='overview-filter-form']",
        title: "常用條件都在上方篩選表單",
        description: "可依日期、單號、治具代碼、datecode/編號等條件縮小結果。如果要追某一筆異常收料，先從日期和治具代碼開始過濾最快。",
        placement: "bottom"
      }
    ]
  },
  {
    id: "master-basics",
    sectionLabel: "主資料維護",
    label: "治具 / 機種主資料",
    summary: "說明從更多功能進入後，如何在清單與表單間維護基礎資料。",
    requiresMasterAccess: true,
    steps: [
      {
        id: "master-menu",
        route: "/search",
        target: "[data-tour='home-more-menu-trigger']",
        title: "主資料維護同樣從更多功能進入",
        description: "這個系統把維護入口集中在首頁同一組選單，避免新手要記多個分散頁面。",
        placement: "bottom",
        openMoreMenu: true
      },
      {
        id: "master-entry",
        route: "/search",
        target: "[data-tour='home-master-entry']",
        title: "點這裡進入資料維護頁",
        description: "進去後可以維護治具、機種、站點等主資料。收退料與產能功能都依賴這裡的基礎資料是否正確。",
        placement: "left",
        openMoreMenu: true
      },
      {
        id: "master-tabs",
        route: "/master",
        target: "[data-tour='master-tabs']",
        title: "先選你要維護的主資料類型",
        description: "上方 tab 決定你目前在維護治具、機種或站點。新增需求前，先確認自己在正確的資料類型下操作。",
        placement: "bottom"
      },
      {
        id: "master-list",
        route: "/master",
        target: "[data-tour='master-list-table']",
        title: "左邊清單用來挑資料，右邊表單用來改資料",
        description: "先從清單選一筆資料，右邊才會帶出對應內容。這是整個系統主資料維護最核心的操作模式。",
        placement: "right"
      },
      {
        id: "master-detail",
        route: "/master",
        target: "[data-tour='master-detail-form']",
        title: "在表單完成新增或修改，最後要記得儲存",
        description: "無論是補治具名稱、機種資訊或站點代碼，最後都要按儲存才會真的寫入。之後收退料與產能頁才會讀到最新設定。",
        placement: "left"
      }
    ]
  },
  {
    id: "production-mapping",
    sectionLabel: "產能管理",
    label: "機種站點對應",
    summary: "具體說明先選機種，再把機種綁到站點的操作順序。",
    steps: [
      {
        id: "production-menu",
        route: "/search",
        target: "[data-tour='home-more-menu-trigger']",
        title: "產能管理入口也在更多功能",
        description: "查詢頁只是入口。要設定站點對應與治具需求，先從首頁打開更多功能再進入產能管理。",
        placement: "bottom",
        openMoreMenu: true
      },
      {
        id: "production-entry",
        route: "/search",
        target: "[data-tour='home-production-entry']",
        title: "從這裡進入產能管理",
        description: "進去後可看總覽、機種站點對應與治具需求。建議先做 Mapping，再做 Requirement。",
        placement: "left",
        openMoreMenu: true
      },
      {
        id: "production-tabs",
        route: "/production/mapping",
        target: "[data-tour='production-tabs']",
        title: "產能頁先分清楚兩種設定",
        description: "`機種站點對應` 是先定義某個機種會經過哪些站點；`治具需求` 則是在既有站點上再綁治具與數量。順序不要顛倒。",
        placement: "bottom"
      },
      {
        id: "production-filter-row",
        route: "/production/mapping",
        target: "[data-tour='production-filter-row']",
        title: "進來先選機種，再進行下面的綁定",
        description: "上方機種下拉會決定你現在是在編輯哪一個機種。切換機種後，下方清單與新增表單都會一起跟著換。",
        placement: "bottom"
      },
      {
        id: "production-mapping-panel",
        route: "/production/mapping",
        target: "[data-tour='production-mapping-panel']",
        title: "這個區塊專門綁機種與站點",
        description: "同一機種可對應多個站點。只要某機種會經過某站，就要先在這裡建立對應，後面的治具需求才有依附基礎。",
        placement: "top"
      },
      {
        id: "production-mapping-form",
        route: "/production/mapping",
        target: "[data-tour='production-mapping-form']",
        title: "輸入機種代碼與站點代碼後直接新增",
        description: "兩個欄位都支援輸入後下拉選擇。選好機種和站點後按 `新增 / 更新`，就完成一筆機種站點綁定。",
        placement: "top"
      },
      {
        id: "production-mapping-list",
        route: "/production/mapping",
        target: "[data-tour='production-mapping-list']",
        title: "新增完要看下面清單是否真的出現",
        description: "表格會列出目前機種已綁定的站點。若有打錯，可直接在這裡編輯或刪除；要大量匯入則用上方的批次貼上匯入。",
        placement: "top"
      }
    ]
  },
  {
    id: "production-requirements",
    sectionLabel: "產能管理",
    label: "站點治具需求",
    summary: "具體說明先有 Mapping，再在站點上綁治具與需求數量。",
    steps: [
      {
        id: "production-menu",
        route: "/search",
        target: "[data-tour='home-more-menu-trigger']",
        title: "需求設定前，先回到產能管理入口",
        description: "治具需求是產能頁的另一個分頁，但一樣從首頁更多功能進入，避免新手不知道切去哪裡。",
        placement: "bottom",
        openMoreMenu: true
      },
      {
        id: "production-entry",
        route: "/search",
        target: "[data-tour='home-production-entry']",
        title: "需求設定也從這裡進入產能管理",
        description: "如果你是從查詢頁直接來設定站點用治具，先進產能頁，再切到 `治具需求` 分頁。",
        placement: "left",
        openMoreMenu: true
      },
      {
        id: "production-tabs",
        route: "/production/requirements",
        target: "[data-tour='production-tabs']",
        title: "治具需求之前，先確保 Mapping 已建好",
        description: "這兩個分頁有先後關係。若 `機種站點對應` 還沒建立，`治具需求` 裡就不會有可選站點可以綁治具。",
        placement: "bottom"
      },
      {
        id: "production-filter-row",
        route: "/production/requirements",
        target: "[data-tour='production-filter-row']",
        title: "先選機種，再針對該機種下的站點設定需求",
        description: "切換機種後，需求表單只會列出這個機種已經綁定好的站點。若站點下拉為空，表示先回 Mapping 補綁定。",
        placement: "bottom"
      },
      {
        id: "production-requirement-panel",
        route: "/production/requirements",
        target: "[data-tour='production-requirement-panel']",
        title: "這個區塊負責綁站點、治具與需求數量",
        description: "每一筆需求都代表某機種在某站點需要幾套治具。這裡設定完，後續產能分析才知道哪個治具可能成為瓶頸。",
        placement: "top"
      },
      {
        id: "production-requirement-form",
        route: "/production/requirements",
        target: "[data-tour='production-requirement-form']",
        title: "操作順序是先站點，再治具，最後數量",
        description: "先選站點，再選治具代碼，最後填需要的數量。站點欄位只接受目前機種已綁定的站點，避免在錯誤站點上建立需求。",
        placement: "top"
      },
      {
        id: "production-requirement-list",
        route: "/production/requirements",
        target: "[data-tour='production-requirement-list']",
        title: "新增後在列表核對站點、治具與數量",
        description: "下方表格就是目前站點的正式需求清單。若數量錯了或綁錯治具，可直接編輯；大量新增則走批次貼上匯入。",
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
