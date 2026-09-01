import fs from "node:fs/promises";
import path from "node:path";
import { FileBlob, PresentationFile } from "@oai/artifact-tool";

const TMP_DIR = "C:/Users/user/PycharmProjects/jig-record/.codex-temp/jig-system-deck-detail-20260803";
const SOURCE_PPTX = `${TMP_DIR}/template-starter.pptx`;
const FINAL_PPTX = "C:/Users/user/PycharmProjects/jig-record/治具系統_功能場景效益_詳細版.pptx";
const FONT = "Microsoft JhengHei";
const INK = "#111827";
const MUTED = "#4B5563";
const BLUE = "#1D4ED8";

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

function featureBlock(heading, details) {
  const runs = [
    {
      run: heading,
      textStyle: { fontSize: "30px", typeface: FONT, color: INK, bold: true },
    },
  ];
  for (const detail of details) {
    runs.push({
      run: `\n${detail}`,
      textStyle: { fontSize: "22px", typeface: FONT, color: MUTED },
    });
  }
  return { runs, paragraphStyle: { lineSpacingPercent: 116000 } };
}

function benefitBlock() {
  return {
    runs: [
      {
        run: "減少等待｜圖片、庫位、庫存與關聯機種集中查詢，縮短找料與問人時間。",
        textStyle: { fontSize: "24px", typeface: FONT, color: MUTED },
      },
      {
        run: "\n\n降低風險｜低庫存／缺料提前提示，收退料可追溯，減少帳實不符。",
        textStyle: { fontSize: "24px", typeface: FONT, color: MUTED },
      },
      {
        run: "\n\n提升規劃｜依機種、工站與需求量試算可開站數，提早辨識瓶頸。",
        textStyle: { fontSize: "24px", typeface: FONT, color: MUTED },
      },
      {
        run: "\n\n建議量測｜查找時間、缺料事件、排程調整次數",
        textStyle: { fontSize: "20px", typeface: FONT, color: BLUE, bold: true },
      },
    ],
    paragraphStyle: { lineSpacingPercent: 122000 },
  };
}

async function writeBlob(filePath, blob) {
  await fs.mkdir(path.dirname(filePath), { recursive: true });
  await fs.writeFile(filePath, new Uint8Array(await blob.arrayBuffer()));
}

function parseInspect(ndjson) {
  return ndjson
    .split(/\r?\n/)
    .filter(Boolean)
    .map((line) => JSON.parse(line));
}

function exactRecord(records, kind, slide, name) {
  const matches = records.filter(
    (record) => record.kind === kind && record.slide === slide && record.name === name,
  );
  if (matches.length !== 1) {
    throw new Error(`Expected one ${kind} on slide ${slide} named ${name}; found ${matches.length}.`);
  }
  return matches[0];
}

async function main() {
  const presentation = await PresentationFile.importPptx(await FileBlob.load(SOURCE_PPTX));
  const before = await presentation.inspect({
    kind: "slide,textbox,shape,image,notes,layout",
    include: "id,slide,name,text,textPreview,bbox,title,alt,isPlaceholder",
    maxChars: 30000,
  });
  await fs.writeFile(`${TMP_DIR}/before-inspect.ndjson`, before.ndjson, "utf8");
  const records = parseInspect(before.ndjson);

  const slide1Title = presentation.resolve(
    exactRecord(records, "textbox", 1, "Google-Shape-533-p58-3").id,
  );
  const slide1Search = presentation.resolve(
    exactRecord(records, "textbox", 1, "Google-Shape-558-p61-4").id,
  );
  const slide1Inventory = presentation.resolve(
    exactRecord(records, "textbox", 1, "Google-Shape-559-p61-5").id,
  );
  const slide1Capacity = presentation.resolve(
    exactRecord(records, "textbox", 1, "Google-Shape-560-p61-6").id,
  );

  slide1Title.text = rich("治具系統，串起查找、庫存與產能", 50, { bold: true });
  slide1Search.text = featureBlock("快速查找", [
    "搜尋｜編號／名稱、機種、工站或庫位",
    "顯示｜照片、庫存、關聯機種與責任人",
  ]);
  slide1Inventory.text = featureBlock("庫存管理", [
    "作業｜收料、退料、批次貼上、CSV 匯入",
    "狀態｜庫存摘要、低庫存／無庫存提示",
  ]);
  slide1Capacity.text = featureBlock("產能規劃", [
    "設定｜機種 × 工站 × 治具需求量",
    "計算｜取可支援數最小值，得到最大開站能力",
  ]);

  const slide2Timeline = presentation.resolve(
    exactRecord(records, "shape", 2, "Google-Shape-2259-p159-4").id,
  );
  slide2Timeline.position = { left: 35.46, top: 560.8, width: 1203.21, height: 0.03 };

  const slide3Title = presentation.resolve(
    exactRecord(records, "textbox", 3, "Google-Shape-533-p58-3").id,
  );
  const slide3Lead = presentation.resolve(
    exactRecord(records, "textbox", 3, "Google-Shape-534-p58-4").id,
  );
  const slide3Benefits = presentation.resolve(
    exactRecord(records, "textbox", 3, "TextBox-11-7").id,
  );

  slide3Title.text = rich("系統功能直接改善等待、缺料與排程風險", 50, { bold: true });
  slide3Lead.text = rich("五項系統作法，建立一致作業依據", 32, { bold: true });
  slide3Benefits.text = benefitBlock();

  const slide1 = presentation.resolve(records.find((record) => record.kind === "slide" && record.slide === 1).id);
  const slide3 = presentation.resolve(records.find((record) => record.kind === "slide" && record.slide === 3).id);
  slide1.speakerNotes.append("\n補充：功能介紹已展開至搜尋欄位、顯示資訊、收退料／批次作業、警示與產能計算邏輯。");
  slide3.speakerNotes.append("\n補充：改善效益以等待、缺料風險與排程判斷三類結果呈現，並保留導入後量測建議。");

  for (const [index, slide] of presentation.slides.items.entries()) {
    const stem = `final-slide-${String(index + 1).padStart(2, "0")}`;
    await writeBlob(`${TMP_DIR}/${stem}.png`, await presentation.export({ slide, format: "png", scale: 2 }));
    const layout = await slide.export({ format: "layout" });
    await fs.writeFile(`${TMP_DIR}/${stem}.layout.json`, await layout.text(), "utf8");
  }

  const after = await presentation.inspect({
    kind: "slide,textbox,shape,image,notes,layout",
    include: "id,slide,name,text,textPreview,bbox,title,alt,isPlaceholder",
    maxChars: 30000,
  });
  await fs.writeFile(`${TMP_DIR}/after-inspect.ndjson`, after.ndjson, "utf8");

  const pptx = await PresentationFile.exportPptx(presentation);
  await pptx.save(FINAL_PPTX);
  console.log(FINAL_PPTX);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
