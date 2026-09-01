import fs from "node:fs/promises";
import path from "node:path";
import { Presentation, PresentationFile } from "@oai/artifact-tool";
import { buildSlide07 } from "./slide-07.mjs";
import { buildSlide18 } from "./slide-18.mjs";
import { buildSlide10 } from "./slide-10.mjs";

const TMP_DIR = "C:/Users/user/PycharmProjects/jig-record/.codex-temp/jig-system-deck-20260803";
const FINAL_PPTX = "C:/Users/user/PycharmProjects/jig-record/治具系統_功能場景效益.pptx";
const FONT = "Microsoft JhengHei";
const INK = "#111827";
const MUTED = "#4B5563";
const ACCENT = "#3D8DFF";

function rich(text, fontSize, options = {}) {
  return {
    runs: [
      {
        run: text,
        textStyle: {
          fontSize: `${fontSize}px`,
          typeface: FONT,
          color: options.color ?? INK,
          bold: options.bold ?? false,
        },
      },
    ],
    paragraphStyle: { lineSpacingPercent: options.lineSpacingPercent ?? 112000 },
  };
}

function featureBlock(heading, detail) {
  return {
    runs: [
      {
        run: heading,
        textStyle: { fontSize: "30px", typeface: FONT, color: INK, bold: true },
      },
      {
        run: `\n${detail}`,
        textStyle: { fontSize: "22px", typeface: FONT, color: MUTED },
      },
    ],
    paragraphStyle: { lineSpacingPercent: 118000 },
  };
}

function scenarioBlock(heading, detail) {
  return {
    titleHere: rich(heading, 32, { bold: true }),
    loremIpsumDolorSitAmetConsecteturAdipiscing: rich(detail, 22, {
      color: MUTED,
      lineSpacingPercent: 122000,
    }),
  };
}

async function imageBytes(imagePath) {
  const bytes = await fs.readFile(imagePath);
  return bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);
}

function addAccentRule(slide) {
  slide.shapes.add({
    geometry: "rect",
    name: "accent-rule",
    position: { left: 41.33, top: 136, width: 176, height: 5 },
    fill: ACCENT,
    line: { style: "solid", fill: ACCENT, width: 0 },
  });
}

async function addFixturePhoto(slide, imagePath, position, alt, name) {
  slide.shapes.add({
    geometry: "rect",
    name: `${name}-frame`,
    position: {
      left: position.left - 4,
      top: position.top - 4,
      width: position.width + 8,
      height: position.height + 8,
    },
    fill: "#EDEDED",
    line: { style: "solid", fill: "#D1D5DB", width: 1 },
  });
  slide.images.add({
    blob: await imageBytes(imagePath),
    contentType: "image/jpeg",
    alt,
    name,
    fit: "cover",
    position,
  });
}

function setNotes(slide, lines) {
  slide.speakerNotes.textFrame.setText(lines.join("\n"));
  slide.speakerNotes.setVisible(true);
}

async function writeBlob(filePath, blob) {
  await fs.mkdir(path.dirname(filePath), { recursive: true });
  await fs.writeFile(filePath, new Uint8Array(await blob.arrayBuffer()));
}

async function main() {
  const presentation = Presentation.create({ slideSize: { width: 1280, height: 720 } });

  const slide1 = buildSlide07(presentation, {
    footer1: "01 / 03",
    title: rich("治具系統，把查找、庫存與產能串在一起", 50, { bold: true }),
    body1: featureBlock("快速查找", "治具、機種、工站與庫位一站定位"),
    body2: featureBlock("庫存管理", "收料／退料、批次匯入與低庫存警示"),
    body3: featureBlock("產能規劃", "依機種＋工站換算最大可開站數"),
  });
  addAccentRule(slide1);
  await addFixturePhoto(
    slide1,
    "C:/Users/user/PycharmProjects/jig-record/uploads/fixtures/O-78-5.jpg",
    { left: 41.33, top: 174, width: 374.67, height: 148 },
    "治具實物與識別標籤範例",
    "fixture-photo-search",
  );
  await addFixturePhoto(
    slide1,
    "C:/Users/user/PycharmProjects/jig-record/uploads/fixtures/F-00629.jpg",
    { left: 453.33, top: 174, width: 374.67, height: 148 },
    "治具實物照片範例",
    "fixture-photo-inventory",
  );
  await addFixturePhoto(
    slide1,
    "C:/Users/user/PycharmProjects/jig-record/uploads/fixtures/D-00002.jpg",
    { left: 864.28, top: 174, width: 374.67, height: 148 },
    "附識別碼的治具實物範例",
    "fixture-photo-capacity",
  );
  setNotes(slide1, [
    "主旨：系統把原本分散的治具資料、庫存狀態與生產需求放進同一個操作流程。",
    "[Sources]",
    "- C:/Users/user/PycharmProjects/jig-record/AGENT.md（系統定位、搜尋、庫存與產能計算）",
    "- C:/Users/user/PycharmProjects/jig-record/ARCHITECTURE_LANDING.md（目前已實作功能）",
    "- C:/Users/user/PycharmProjects/jig-record/uploads/fixtures/O-78-5.jpg",
    "- C:/Users/user/PycharmProjects/jig-record/uploads/fixtures/F-00629.jpg",
    "- C:/Users/user/PycharmProjects/jig-record/uploads/fixtures/D-00002.jpg",
  ]);

  const slide2 = buildSlide18(presentation, {
    footer1: "02 / 03",
    title: rich("三個現場節點，快速完成日常決策", 50, { bold: true }),
    body1: scenarioBlock("開工前備料", "搜尋治具與庫位，確認庫存與責任人，快速備齊現場需求。"),
    body2: scenarioBlock("缺料異常處理", "遇到低庫存或缺料，追溯收退料明細，補料與責任歸屬更清楚。"),
    body3: scenarioBlock("生產排程確認", "選定機種與工站，依需求量與現有庫存估算最大可開站數。"),
    label1: rich("01｜班前準備", 19, { bold: true, color: ACCENT }),
    label2: rich("02｜缺料應變", 19, { bold: true, color: ACCENT }),
    label3: rich("03｜排程確認", 19, { bold: true, color: ACCENT }),
  });
  addAccentRule(slide2);
  setNotes(slide2, [
    "使用方式可依現場節奏說明：班前確認、異常應變、排程決策。",
    "最大可開站數的核心邏輯為各必要治具可支援數量的最小值；查詢範圍必須包含機種與工站。",
    "[Sources]",
    "- C:/Users/user/PycharmProjects/jig-record/AGENT.md（搜尋規則、庫存警示、產能計算）",
    "- C:/Users/user/PycharmProjects/jig-record/ARCHITECTURE_LANDING.md（搜尋、收退料、批次與產能功能）",
  ]);

  const slide3 = buildSlide10(presentation, {
    footer1: "03 / 03",
    title: rich("治具系統，少掉三種現場浪費", 50, { bold: true }),
    body1: rich("把分散的現場資訊，變成一致的作業依據", 32, { bold: true }),
    body2: {
      loremIpsumDolorSitAmetConsecteturAdipiscing: rich(
        "減少等待｜不用反覆找治具、問庫位、核對庫存。\n\n降低重工｜收退料、責任與權限都有一致紀錄。\n\n提升判斷｜用實際庫存與需求量支援備料與排程。",
        24,
        { color: MUTED, lineSpacingPercent: 125000 },
      ),
      loremIpsumDolorSitAmetConsecteturAdipiscing2: rich(
        "\n建議追蹤：平均查找時間、缺料事件、排程調整次數",
        20,
        { color: "#1D4ED8", bold: true, lineSpacingPercent: 118000 },
      ),
    },
    label1: rich("查找｜圖片與庫位", 32, { bold: true }),
    label2: rich("預警｜低庫存提示", 32, { bold: true }),
    label3: rich("規劃｜可開站試算", 32, { bold: true }),
    label4: rich("權責｜角色與稽核", 32, { bold: true }),
    label5: rich("資料｜批次匯入匯出", 32, { bold: true }),
  });
  addAccentRule(slide3);
  setNotes(slide3, [
    "效益以可驗證的改善方向呈現，避免在尚未建立基準值前宣稱百分比成果。",
    "建議導入前後用相同口徑追蹤：平均查找時間、缺料事件數、排程調整次數。",
    "[Sources]",
    "- C:/Users/user/PycharmProjects/jig-record/AGENT.md（系統目標、權限、庫存警示、產能規劃）",
    "- C:/Users/user/PycharmProjects/jig-record/ARCHITECTURE_LANDING.md（現有功能與使用範圍）",
  ]);

  for (const [index, slide] of presentation.slides.items.entries()) {
    const stem = `slide-${String(index + 1).padStart(2, "0")}`;
    await writeBlob(path.join(TMP_DIR, `${stem}.png`), await presentation.export({ slide, format: "png", scale: 2 }));
    const layout = await slide.export({ format: "layout" });
    await fs.writeFile(path.join(TMP_DIR, `${stem}.layout.json`), await layout.text(), "utf8");
  }

  await writeBlob(
    path.join(TMP_DIR, "deck-montage.webp"),
    await presentation.export({ format: "webp", montage: true, scale: 1 }),
  );
  const pptx = await PresentationFile.exportPptx(presentation);
  await pptx.save(FINAL_PPTX);

  const inspection = await presentation.inspect({
    kind: "slide,textbox,shape,image",
    maxChars: 12000,
  });
  await fs.writeFile(path.join(TMP_DIR, "inspection.ndjson"), inspection.ndjson, "utf8");
  console.log(FINAL_PPTX);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
