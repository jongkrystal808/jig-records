export type TourPlacement = "top" | "bottom" | "left" | "right";

export interface OnboardingStep {
  id: string;
  route: string;
  target: string;
  title: string;
  description: string;
  placement?: TourPlacement;
}

export const onboardingSteps: OnboardingStep[] = [
  {
    id: "search-onboarding-entry",
    route: "/search",
    target: "[data-tour='search-onboarding-entry']",
    title: "需要時可從首頁重播教學",
    description: "首頁提供固定的新手教學入口。第一次登入會自動啟動，之後也可以從這裡重新播放。",
    placement: "bottom"
  },
  {
    id: "search-mode",
    route: "/search",
    target: "[data-tour='search-mode-switch']",
    title: "首頁先從查詢開始",
    description: "這是首頁的查詢入口，可以切換治具或機種查詢，是大部分使用者最常用的起點。",
    placement: "bottom"
  },
  {
    id: "search-input",
    route: "/search",
    target: "[data-tour='search-query-field']",
    title: "在這裡輸入關鍵字",
    description: "輸入治具編號、名稱或機種代碼後就能快速定位資料。教學時建議先示範查詢既有資料。",
    placement: "bottom"
  },
  {
    id: "search-sections",
    route: "/search",
    target: "[data-tour='search-section-chips']",
    title: "結果區塊可以自由切換",
    description: "這些區塊決定你想看總覽、圖片、收退料或維護資訊，方便依角色調整畫面。",
    placement: "bottom"
  },
  {
    id: "inventory-entry",
    route: "/search",
    target: "[data-tour='inventory-entry-trigger']",
    title: "收退料從首頁頂部入口進入",
    description: "你目前的主要收退料流程是從這個按鈕開啟，不需要先切頁。",
    placement: "bottom"
  },
  {
    id: "inventory-mode",
    route: "/search",
    target: "[data-tour='inventory-mode-switch']",
    title: "先決定是收料還是退料",
    description: "開啟收退料視窗後，先在這裡切換模式，再開始後續操作。",
    placement: "bottom"
  },
  {
    id: "inventory-batch",
    route: "/search",
    target: "[data-tour='inventory-batch-panel']",
    title: "這裡是收退料主要操作區",
    description: "收退料主要都在這個區塊完成，包括單號、備註、批次內容與解析結果。",
    placement: "right"
  },
  {
    id: "inventory-paste",
    route: "/search",
    target: "[data-tour='inventory-paste-field']",
    title: "確認貼上的收退料內容",
    description: "正式使用時，會把批次內容貼在這裡，系統會自動解析成下方預覽。",
    placement: "left"
  },
  {
    id: "inventory-submit",
    route: "/search",
    target: "[data-tour='inventory-submit-action']",
    title: "確認無誤後再送出",
    description: "確認解析結果無誤後，再按這個送出按鈕把收料或退料資料寫入系統。",
    placement: "top"
  },
  {
    id: "export-entry",
    route: "/search",
    target: "[data-tour='inventory-export-entry-trigger']",
    title: "收退料資訊匯出也從首頁進入",
    description: "如果要下載收退料報表，直接從首頁這個按鈕開啟匯出視窗。",
    placement: "bottom"
  },
  {
    id: "export-panel",
    route: "/search",
    target: "[data-tour='inventory-export-panel']",
    title: "在這裡設定匯出條件",
    description: "可以選報表類型、日期範圍與篩選條件，再決定要輸出成什麼格式。",
    placement: "left"
  },
  {
    id: "menu-trigger",
    route: "/search",
    target: "[data-tour='home-more-menu-trigger']",
    title: "其他功能從首頁的更多功能進入",
    description: "收退料總檢視、資料維護與產能管理都從這個入口展開。",
    placement: "bottom"
  },
  {
    id: "overview-entry",
    route: "/search",
    target: "[data-tour='home-overview-entry']",
    title: "先從這裡進入收退料總檢視",
    description: "這個入口會帶你到收退料總檢視頁，看歷史紀錄與條件查詢。",
    placement: "left"
  },
  {
    id: "overview-page",
    route: "/inventory/overview",
    target: "[data-tour='overview-page-head']",
    title: "這是收退料總檢視",
    description: "你可以在這裡查看全體收退料紀錄與目前查詢範圍。",
    placement: "bottom"
  },
  {
    id: "overview-filters",
    route: "/inventory/overview",
    target: "[data-tour='overview-filter-form']",
    title: "用條件篩選歷史紀錄",
    description: "可依日期、單號、治具編號或識別碼縮小查詢範圍。",
    placement: "bottom"
  },
  {
    id: "master-entry",
    route: "/search",
    target: "[data-tour='home-master-entry']",
    title: "再從首頁進入資料維護",
    description: "主資料維護也是從更多功能進入，不會直接跳頁讓使用者找不到入口。",
    placement: "left"
  },
  {
    id: "master-tabs",
    route: "/master",
    target: "[data-tour='master-tabs']",
    title: "主資料維護集中在這裡",
    description: "這裡可以切換治具、機種、站點等主資料，是建立基礎資料的地方。",
    placement: "bottom"
  },
  {
    id: "master-list",
    route: "/master",
    target: "[data-tour='master-list-table']",
    title: "左邊清單，右邊表單",
    description: "點左邊任一筆資料，右邊就會帶出詳細資料。這是整個系統最核心的操作模式。",
    placement: "right"
  },
  {
    id: "master-detail",
    route: "/master",
    target: "[data-tour='master-detail-form']",
    title: "在表單區修改或新增資料",
    description: "欄位改完後記得按儲存，這樣資料才會真正寫入系統。",
    placement: "left"
  },
  {
    id: "production-entry",
    route: "/search",
    target: "[data-tour='home-production-entry']",
    title: "最後從首頁進入產能管理",
    description: "產能管理同樣建議從首頁入口開始，讓新手建立完整使用路徑。",
    placement: "left"
  },
  {
    id: "production-tabs",
    route: "/production",
    target: "[data-tour='production-tabs']",
    title: "產能管理也有導覽",
    description: "最後帶你到產能管理，這裡可以查看站點對應、需求設定與瓶頸分析。",
    placement: "bottom"
  },
  {
    id: "production-filters",
    route: "/production",
    target: "[data-tour='production-filter-row']",
    title: "先選模型與站點再看分析",
    description: "切到這頁後，先確認目前模型與站點，系統才會顯示正確的產能與需求結果。",
    placement: "bottom"
  }
];
