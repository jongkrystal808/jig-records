import { Presentation, PresentationFile } from "@oai/artifact-tool";
import fs from "node:fs/promises";

const OUT = "C:/Users/user/PycharmProjects/jig-record/artifacts/Fixture-M_Lite_治具系統改善簡報.pptx";
const ROOT = "C:/Users/user/PycharmProjects/jig-record";

const COLORS = {
  canvas: "#E5E7EF",
  white: "#FFFFFF",
  ink: "#111827",
  muted: "#64748B",
  border: "#171717",
  blue: "#2563EB",
  blueDark: "#1E3A8A",
  bluePale: "#EFF6FF",
  rust: "#B43216",
  rustPale: "#FFF4EF",
  grid: "#90A074",
  tableFill: "#F1F4EE",
  footer: "#D8D9DE",
  footerBand: "#BFC2CA",
};

const FONT = "Microsoft JhengHei";

function addShape(slide, name, geometry, position, fill = "none", lineFill = "none", lineWidth = 0, radius) {
  return slide.shapes.add({
    geometry,
    name,
    position,
    fill,
    line: { style: "solid", fill: lineFill, width: lineWidth },
    ...(radius ? { borderRadius: radius } : {}),
  });
}

function addText(slide, name, text, position, opts = {}) {
  const box = addShape(slide, name, "textbox", position, opts.fill ?? "none", opts.lineFill ?? "none", opts.lineWidth ?? 0, opts.radius);
  box.text = text;
  box.text.style = {
    fontFamily: FONT,
    fontSize: opts.fontSize ?? 18,
    bold: opts.bold ?? false,
    color: opts.color ?? COLORS.ink,
    alignment: opts.alignment ?? "left",
  };
  return box;
}

function addLine(slide, name, x, y, width, color = COLORS.border, lineWidth = 2) {
  return addShape(slide, name, "line", { left: x, top: y, width, height: 0 }, "none", color, lineWidth);
}

function addFooter(slide, index) {
  addShape(slide, `footer-${index}`, "rect", { left: 0, top: 858, width: 1280, height: 102 }, COLORS.footer, "none", 0);
  addShape(slide, `footer-band-${index}`, "roundRect", { left: 355, top: 886, width: 810, height: 36 }, COLORS.footerBand, "none", 0, 18);
  addShape(slide, `footer-logo-${index}`, "rect", { left: 48, top: 875, width: 64, height: 50 }, COLORS.white, "none", 0);
  addText(slide, `footer-logo-text-${index}`, "FM", { left: 51, top: 888, width: 58, height: 26 }, { fontSize: 19, bold: true, color: COLORS.blue, alignment: "center" });
  addText(slide, `footer-brand-${index}`, "Fixture-M Lite", { left: 124, top: 874, width: 220, height: 34 }, { fontSize: 22, bold: true, color: COLORS.ink });
  addText(slide, `footer-sub-${index}`, "治具庫存與產能管理平台", { left: 126, top: 907, width: 220, height: 20 }, { fontSize: 11, color: COLORS.muted });
  addText(slide, `footer-page-${index}`, String(index).padStart(2, "0"), { left: 1180, top: 889, width: 56, height: 28 }, { fontSize: 16, bold: true, color: "#4B5563", alignment: "center" });
}

function addCostTable(slide, rows, index) {
  const x = 48;
  const y = 646;
  const widths = [108, 538, 538];
  const heights = [38, 52, 52, 52];
  const values = [
    ["改善項目", "改善前", "改善後"],
    ["人力成本", rows[0][0], rows[0][1]],
    ["錯誤成本", rows[1][0], rows[1][1]],
    ["操作成本", rows[2][0], rows[2][1]],
  ];
  let top = y;
  for (let r = 0; r < 4; r += 1) {
    let left = x;
    for (let c = 0; c < 3; c += 1) {
      addShape(slide, `cost-cell-${index}-${r}-${c}`, "rect", { left, top, width: widths[c], height: heights[r] }, COLORS.tableFill, COLORS.grid, 1);
      addText(slide, `cost-text-${index}-${r}-${c}`, values[r][c], { left: left + 8, top: top + (r === 0 ? 8 : 9), width: widths[c] - 16, height: heights[r] - 12 }, {
        fontSize: r === 0 ? 15 : 14,
        bold: c === 0 || r === 0,
        color: r === 0 ? COLORS.ink : "#263238",
        alignment: c === 0 ? "left" : "left",
      });
      left += widths[c];
    }
    top += heights[r];
  }
}

function addBeforePanel(slide, slideNo, headline, bullets, keywords) {
  addShape(slide, `before-surface-${slideNo}`, "rect", { left: 49, top: 254, width: 591, height: 392 }, "#FCFCFD", "none", 0);
  addShape(slide, `before-accent-${slideNo}`, "rect", { left: 72, top: 282, width: 8, height: 266 }, COLORS.rust, "none", 0);
  addText(slide, `before-headline-${slideNo}`, headline, { left: 98, top: 278, width: 500, height: 58 }, { fontSize: 27, bold: true, color: COLORS.rust });
  addText(slide, `before-bullets-${slideNo}`, bullets.map((item) => `• ${item}`).join("\n\n"), { left: 98, top: 345, width: 492, height: 190 }, { fontSize: 18, color: COLORS.ink });
  addShape(slide, `before-keywords-bg-${slideNo}`, "roundRect", { left: 96, top: 566, width: 480, height: 48 }, COLORS.rustPale, "#F0B7A5", 1, 12);
  addText(slide, `before-keywords-${slideNo}`, keywords, { left: 108, top: 578, width: 456, height: 26 }, { fontSize: 16, bold: true, color: "#8C2B17", alignment: "center" });
}

function addAfterScreenshot(slide, slideNo, imageBytes, alt, caption) {
  addShape(slide, `after-surface-${slideNo}`, "rect", { left: 640, top: 254, width: 591, height: 392 }, COLORS.white, "none", 0);
  addShape(slide, `after-frame-${slideNo}`, "roundRect", { left: 666, top: 274, width: 540, height: 302 }, COLORS.bluePale, "#9CB9F5", 1, 12);
  slide.images.add({
    blob: imageBytes,
    contentType: "image/png",
    alt,
    fit: "cover",
    geometry: "roundRect",
    borderRadius: 10,
    position: { left: 674, top: 282, width: 524, height: 286 },
  });
  addText(slide, `after-caption-${slideNo}`, caption, { left: 674, top: 586, width: 524, height: 44 }, { fontSize: 17, bold: true, color: COLORS.blueDark, alignment: "center" });
}

function addAfterCapacity(slide, slideNo) {
  addShape(slide, `after-surface-${slideNo}`, "rect", { left: 640, top: 254, width: 591, height: 392 }, COLORS.white, "none", 0);
  addShape(slide, `capacity-formula-bg-${slideNo}`, "roundRect", { left: 680, top: 284, width: 510, height: 126 }, COLORS.bluePale, "#9CB9F5", 1, 14);
  addText(slide, `capacity-label-${slideNo}`, "權威可開站數", { left: 710, top: 298, width: 450, height: 30 }, { fontSize: 18, bold: true, color: COLORS.blueDark, alignment: "center" });
  addText(slide, `capacity-formula-${slideNo}`, "MIN  ⌊目前庫存 ÷ 單站需求量⌋", { left: 698, top: 338, width: 474, height: 52 }, { fontSize: 28, bold: true, color: COLORS.blue, alignment: "center" });
  addText(slide, `capacity-scope-${slideNo}`, "計算範圍：model_id + station_id 的完整治具需求集合", { left: 682, top: 425, width: 506, height: 38 }, { fontSize: 17, bold: true, color: COLORS.ink, alignment: "center" });
  addText(slide, `capacity-points-${slideNo}`, "✓ 同一站點可被多機種共用，但需求保持機種別\n\n✓ 不再從 station_id 單獨反推機種\n\n✓ 以瓶頸治具決定最大開站數", { left: 704, top: 472, width: 466, height: 132 }, { fontSize: 17, color: COLORS.ink });
}

function addSlideFrame(slide, spec, index) {
  slide.background.fill = COLORS.canvas;
  addShape(slide, `left-accent-${index}`, "rect", { left: 0, top: 103, width: 50, height: 69 }, COLORS.rust, "none", 0);
  addShape(slide, `outer-${index}`, "rect", { left: 48, top: 30, width: 1184, height: 812 }, COLORS.white, COLORS.border, 2);

  addText(slide, `owner-${index}`, "TE－專案改善", { left: 64, top: 76, width: 235, height: 30 }, { fontSize: 18, bold: true });
  addText(slide, `title-${index}`, spec.title, { left: 300, top: 52, width: 680, height: 52 }, { fontSize: 33, bold: true, color: COLORS.ink, alignment: "center" });
  addText(slide, `module-${index}`, spec.module, { left: 1010, top: 68, width: 190, height: 28 }, { fontSize: 14, bold: true, color: COLORS.blueDark, alignment: "right" });
  addLine(slide, `header-line-${index}`, 48, 121, 1184, COLORS.border, 2);

  addText(slide, `reason-label-${index}`, "改善原因：", { left: 62, top: 151, width: 120, height: 30 }, { fontSize: 19, bold: true });
  addText(slide, `reason-${index}`, spec.reason, { left: 178, top: 143, width: 1018, height: 50 }, { fontSize: 18, color: COLORS.ink });
  addLine(slide, `reason-line-${index}`, 48, 208, 1184, COLORS.border, 2);

  addText(slide, `before-label-${index}`, "改善前", { left: 48, top: 214, width: 592, height: 30 }, { fontSize: 21, bold: true, alignment: "center" });
  addText(slide, `after-label-${index}`, "改善後", { left: 640, top: 214, width: 592, height: 30 }, { fontSize: 21, bold: true, alignment: "center" });
  addLine(slide, `panel-top-${index}`, 48, 252, 1184, COLORS.border, 2);
  addShape(slide, `panel-divider-${index}`, "line", { left: 640, top: 208, width: 0, height: 438 }, "none", COLORS.border, 2);

  addBeforePanel(slide, index, spec.beforeHeadline, spec.beforeBullets, spec.beforeKeywords);
  if (spec.afterType === "capacity") {
    addAfterCapacity(slide, index);
  } else {
    addAfterScreenshot(slide, index, spec.imageBytes, spec.alt, spec.caption);
  }

  addCostTable(slide, spec.costs, index);
  addFooter(slide, index);
  slide.speakerNotes.textFrame.setText(spec.notes);
}

const shots = {
  receipt: `${ROOT}/frontend/tests/visual/workbench.visual.spec.ts-snapshots/workbench-receipt-desktop-1920-win32.png`,
  ledger: `${ROOT}/frontend/tests/visual/workbench.visual.spec.ts-snapshots/workbench-ledger-multiselect-open-desktop-1920-win32.png`,
  overview: `${ROOT}/frontend/tests/visual/workbench.visual.spec.ts-snapshots/workbench-management-overview-desktop-1920-win32.png`,
  image: `${ROOT}/frontend/tests/visual/workbench.visual.spec.ts-snapshots/workbench-image-maintenance-desktop-1920-win32.png`,
};

const slides = [
  {
    title: "現場作業集中到同一治具工作台",
    module: "改善總覽",
    reason: "庫存、查詢、產能與管理資料若分散在不同表單，現場需重複查找與交叉核對，難以快速取得一致答案。",
    beforeHeadline: "資訊分散，流程靠人串接",
    beforeBullets: ["收退料、庫存與產能分別查找", "同一欄位在不同流程可能出現不同寫法", "管理者與現場人員缺少一致的操作入口"],
    beforeKeywords: "多處查找　｜　重複輸入　｜　口頭確認",
    afterType: "image",
    image: shots.receipt,
    alt: "Fixture-M Lite 現場工作台收退料畫面",
    caption: "搜尋、收退料、近期紀錄與現場資訊整合於同一工作台",
    costs: [
      ["跨頁查資料、人工彙整", "共用工作台與快捷入口，減少來回查找"],
      ["資料口徑不一，需人工核對", "統一契約、後端規則與角色權限"],
      ["功能入口分散，學習路徑長", "Modern／Form／Workbench 共用核心流程"],
    ],
    notes: "[Sources]\n- doc/ARCHITECTURE_LANDING.md\n- doc/ARCHITECTURE.md\n- frontend/tests/visual/workbench.visual.spec.ts-snapshots/workbench-receipt-desktop-1920-win32.png\n[/Sources]",
  },
  {
    title: "收退料由逐筆登錄改為批次校驗",
    module: "庫存管理",
    reason: "大量收料與退料若逐筆輸入，容易在治具編號、datecode／編號、來源與數量欄位發生漏填或格式不一致。",
    beforeHeadline: "逐筆輸入，核對成本高",
    beforeBullets: ["大量資料需要重複鍵入相同欄位", "短數字識別碼可能出現 1、01、0001 等差異", "匯入衝突或錯誤不易在送出前集中確認"],
    beforeKeywords: "逐筆登錄　｜　格式不一　｜　事後修正",
    afterType: "image",
    image: shots.ledger,
    alt: "Fixture-M Lite 收退料帳目篩選與明細畫面",
    caption: "批次貼上、預覽校驗、統一 identifier 規則與帳目追溯",
    costs: [
      ["逐筆登錄與重複核對", "試算表式批次貼上，一次處理多列"],
      ["識別碼格式不一、欄位遺漏", "前後端共用正規化與欄位驗證"],
      ["錯誤送出後才回頭修正", "送出前預覽；衝突與錯誤逐列提示"],
    ],
    notes: "[Sources]\n- doc/ARCHITECTURE_LANDING.md\n- doc/backend-map.md\n- backend/app/utils/identifier_rules.py\n- frontend/src/utils/identifier.ts\n- frontend/tests/visual/workbench.visual.spec.ts-snapshots/workbench-ledger-multiselect-open-desktop-1920-win32.png\n[/Sources]",
  },
  {
    title: "可開站數改由完整需求的瓶頸決定",
    module: "生產能力",
    reason: "同一站點可被多個機種共用；若只依站點或單一治具庫存估算，會忽略機種別需求與真正的瓶頸治具。",
    beforeHeadline: "站點共用造成產能誤判",
    beforeBullets: ["由 station_id 單獨推測機種，需求範圍不完整", "只看部分治具庫存，可能高估可開站數", "需求數量異動缺少明確的衝突確認"],
    beforeKeywords: "範圍不清　｜　局部估算　｜　產能高估",
    afterType: "capacity",
    costs: [
      ["人工逐一比對治具庫存與需求", "系統依 model＋station 自動計算瓶頸"],
      ["機種與站點關係混用", "需求唯一範圍固定為 model＋station＋fixture"],
      ["匯入可能覆蓋既有設定", "預覽衝突，需明確確認才覆寫"],
    ],
    notes: "[Sources]\n- AGENTS.md\n- doc/ARCHITECTURE_LANDING.md\n- doc/backend-map.md\n- backend/tests/test_configuration_report.py\n- backend/app/services/production_service.py\n[/Sources]",
  },
  {
    title: "查詢與報表改為後端一致彙整",
    module: "搜尋／報表",
    reason: "治具、機種、站點、庫存與交易資料若由前端逐頁拼接，容易出現分頁不一致、漏列與匯出結果不同步。",
    beforeHeadline: "前端拼資料，結果難一致",
    beforeBullets: ["跨多個清單查找治具與關聯資訊", "篩選、排序與彙總分散在頁面邏輯", "畫面結果與完整匯出可能採不同資料範圍"],
    beforeKeywords: "跨表查找　｜　分頁漂移　｜　匯出口徑不一",
    afterType: "image",
    image: shots.overview,
    alt: "Fixture-M Lite 後台收退料總檢視與篩選畫面",
    caption: "後端讀模型統一篩選、排序、分頁、彙總與完整匯出",
    costs: [
      ["人工交叉查詢多張清單", "搜尋優先流程與聯動篩選"],
      ["頁面端拼接造成漏列或重複", "專用 repository＋service 產生一致讀模型"],
      ["畫面與匯出需重複操作", "同一篩選條件支援 CSV／XLSX 完整匯出"],
    ],
    notes: "[Sources]\n- doc/ARCHITECTURE_LANDING.md\n- doc/ARCHITECTURE.md\n- backend/app/repositories/configuration_report_repository.py\n- backend/app/services/configuration_report_service.py\n- frontend/tests/visual/workbench.visual.spec.ts-snapshots/workbench-management-overview-desktop-1920-win32.png\n[/Sources]",
  },
  {
    title: "權限、儲位與圖片改為可追溯規則",
    module: "資料治理",
    reason: "治具資料涉及不同客戶、儲位與現場圖片；若只依畫面隱藏或人工命名，可能造成越權、找錯位置或圖片對應錯誤。",
    beforeHeadline: "規則靠約定，風險留在現場",
    beforeBullets: ["管理權限可能被誤解為可跨客戶操作", "單一儲位欄位無法同時表達線邊與部門位置", "圖片命名、替換與刪除缺少一致的客戶範圍"],
    beforeKeywords: "越權風險　｜　儲位模糊　｜　圖片難維護",
    afterType: "image",
    image: shots.image,
    alt: "Fixture-M Lite 治具圖片維護畫面",
    caption: "後端客戶範圍＋雙儲位欄位＋客戶目錄圖片維護",
    costs: [
      ["人工確認客戶、儲位與圖片對應", "指派客戶範圍與治具代碼快速定位"],
      ["只靠前端隱藏，仍可能越權", "所有 API 在後端再次驗證角色與客戶範圍"],
      ["圖片與刪除後歷史難追溯", "客戶別檔案路徑；刪除可保留交易快照"],
    ],
    notes: "[Sources]\n- AGENTS.md\n- doc/ARCHITECTURE_LANDING.md\n- doc/ARCHITECTURE.md\n- backend/app/core/auth.py\n- backend/alembic/versions/0012_split_fixture_storage_columns.py\n- backend/alembic/versions/0014_fixture_deletion.py\n- frontend/tests/visual/workbench.visual.spec.ts-snapshots/workbench-image-maintenance-desktop-1920-win32.png\n[/Sources]",
  },
];

async function main() {
  const presentation = Presentation.create({ slideSize: { width: 1280, height: 960 } });
  const imageCache = new Map();
  for (let i = 0; i < slides.length; i += 1) {
    if (slides[i].image) {
      if (!imageCache.has(slides[i].image)) {
        imageCache.set(slides[i].image, new Uint8Array(await fs.readFile(slides[i].image)));
      }
      slides[i].imageBytes = imageCache.get(slides[i].image);
    }
    const slide = presentation.slides.add();
    addSlideFrame(slide, slides[i], i + 1);
  }
  const pptx = await PresentationFile.exportPptx(presentation);
  await pptx.save(OUT);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
