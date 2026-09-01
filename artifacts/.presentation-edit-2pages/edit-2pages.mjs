import fs from "node:fs/promises";
import { FileBlob, PresentationFile } from "@oai/artifact-tool";

const starter = "C:/Users/user/PycharmProjects/jig-record/artifacts/.presentation-edit-2pages/template-starter.pptx";
const finalPptx = "C:/Users/user/PycharmProjects/jig-record/artifacts/Fixture-M_Lite_治具系統改善簡報_2頁版.pptx";
const qaDir = "C:/Users/user/PycharmProjects/jig-record/artifacts/.presentation-edit-2pages";

async function writeBlob(path, blob) {
  await fs.writeFile(path, new Uint8Array(await blob.arrayBuffer()));
}

function rewrite(slide, name, oldText, newText) {
  const target = slide.shapes.items.find((shape) => shape.name === name);
  if (!target) throw new Error(`Missing inherited shape: ${name}`);
  target.text.replace(oldText, newText);
}

const presentation = await PresentationFile.importPptx(await FileBlob.load(starter));
const s1 = presentation.slides.items[0];
const s2 = presentation.slides.items[1];

// Slide 1 — duplicate of source slide 2. Preserve all typography and geometry.
rewrite(s1, "title-2", "收退料由逐筆登錄改為批次校驗", "現場操作與庫存整合為批次工作台");
rewrite(s1, "module-2", "庫存管理", "現場／庫存");
rewrite(s1, "reason-2", "大量收料與退料若逐筆輸入，容易在治具編號、datecode／編號、來源與數量欄位發生漏填或格式不一致。", "收退料、查詢與庫存若分散處理，會增加重複輸入、格式不一與事後核對，因此整合為共用工作台與批次校驗流程。");
rewrite(s1, "before-headline-2", "逐筆輸入，核對成本高", "分散登錄，重複核對");
rewrite(s1, "before-bullets-2", "大量資料需要重複鍵入相同欄位", "收退料、查詢與庫存分別操作");
rewrite(s1, "before-bullets-2", "短數字識別碼可能出現 1、01、0001 等差異", "datecode／編號格式容易不一致");
rewrite(s1, "before-bullets-2", "匯入衝突或錯誤不易在送出前集中確認", "大量資料需逐筆輸入並事後修正");
rewrite(s1, "before-keywords-2", "逐筆登錄　｜　格式不一　｜　事後修正", "多處查找　｜　逐筆輸入　｜　事後修正");
rewrite(s1, "after-caption-2", "批次貼上、預覽校驗、統一 identifier 規則與帳目追溯", "工作台集中查詢、批次貼上、預覽校驗與帳目追溯");
rewrite(s1, "cost-text-2-1-1", "逐筆登錄與重複核對", "跨頁查找與逐筆登錄");
rewrite(s1, "cost-text-2-1-2", "試算表式批次貼上，一次處理多列", "共用工作台，一次處理多列");
rewrite(s1, "cost-text-2-2-1", "識別碼格式不一、欄位遺漏", "格式不一、欄位漏填");
rewrite(s1, "cost-text-2-2-2", "前後端共用正規化與欄位驗證", "統一 identifier 規則與後端驗證");
rewrite(s1, "cost-text-2-3-1", "錯誤送出後才回頭修正", "送出後才回頭修正");
rewrite(s1, "cost-text-2-3-2", "送出前預覽；衝突與錯誤逐列提示", "送出前預覽，錯誤逐列提示");
rewrite(s1, "footer-page-2", "02", "01");
presentation.slides.items[0].speakerNotes.textFrame.setText("[Sources]\n- doc/ARCHITECTURE_LANDING.md\n- doc/backend-map.md\n- backend/app/utils/identifier_rules.py\n- frontend/src/utils/identifier.ts\n- frontend/tests/visual/workbench.visual.spec.ts-snapshots/workbench-ledger-multiselect-open-desktop-1920-win32.png\n[/Sources]");

// Slide 2 — duplicate of source slide 4. Preserve the report screenshot and frame.
rewrite(s2, "title-4", "查詢與報表改為後端一致彙整", "產能、報表與資料治理同步收斂");
rewrite(s2, "module-4", "搜尋／報表", "產能／治理");
rewrite(s2, "reason-4", "治具、機種、站點、庫存與交易資料若由前端逐頁拼接，容易出現分頁不一致、漏列與匯出結果不同步。", "產能、報表與客戶資料若各自判斷，容易高估可開站數、產生查詢口徑差異，並增加越權與圖片對應風險。");
rewrite(s2, "before-headline-4", "前端拼資料，結果難一致", "判斷分散，答案難一致");
rewrite(s2, "before-bullets-4", "跨多個清單查找治具與關聯資訊", "只看站點或部分庫存，產能可能高估");
rewrite(s2, "before-bullets-4", "篩選、排序與彙總分散在頁面邏輯", "前端拼接篩選、分頁與完整匯出");
rewrite(s2, "before-bullets-4", "畫面結果與完整匯出可能採不同資料範圍", "權限、儲位與圖片維護依賴人工約定");
rewrite(s2, "before-keywords-4", "跨表查找　｜　分頁漂移　｜　匯出口徑不一", "局部估算　｜　口徑不一　｜　治理風險");
rewrite(s2, "after-caption-4", "後端讀模型統一篩選、排序、分頁、彙總與完整匯出", "瓶頸產能＋後端讀模型＋客戶範圍，形成一致可追溯流程");
rewrite(s2, "cost-text-4-1-1", "人工交叉查詢多張清單", "逐一比對需求、報表與客戶資料");
rewrite(s2, "cost-text-4-1-2", "搜尋優先流程與聯動篩選", "系統彙整瓶頸、篩選與客戶範圍");
rewrite(s2, "cost-text-4-2-1", "頁面端拼接造成漏列或重複", "機種站點混用、頁面拼接或越權");
rewrite(s2, "cost-text-4-2-2", "專用 repository＋service 產生一致讀模型", "model＋station 計算；後端驗證 scope");
rewrite(s2, "cost-text-4-3-1", "畫面與匯出需重複操作", "多處維護、畫面與匯出重複操作");
rewrite(s2, "cost-text-4-3-2", "同一篩選條件支援 CSV／XLSX 完整匯出", "一致讀模型、完整匯出與圖片維護");
rewrite(s2, "footer-page-4", "04", "02");
presentation.slides.items[1].speakerNotes.textFrame.setText("[Sources]\n- AGENTS.md\n- doc/ARCHITECTURE_LANDING.md\n- doc/ARCHITECTURE.md\n- doc/backend-map.md\n- backend/app/services/production_service.py\n- backend/app/repositories/configuration_report_repository.py\n- backend/app/core/auth.py\n- frontend/tests/visual/workbench.visual.spec.ts-snapshots/workbench-management-overview-desktop-1920-win32.png\n[/Sources]");

const finalPreview = `${qaDir}/final-preview`;
const finalLayout = `${qaDir}/final-layout/final`;
await fs.mkdir(finalPreview, { recursive: true });
await fs.mkdir(finalLayout, { recursive: true });
for (let i = 0; i < presentation.slides.items.length; i += 1) {
  const slide = presentation.slides.items[i];
  await writeBlob(`${finalPreview}/final-slide-${String(i + 1).padStart(2, "0")}.png`, await presentation.export({ slide, format: "png", scale: 1 }));
  await fs.writeFile(`${finalLayout}/final-slide-${String(i + 1).padStart(2, "0")}.layout.json`, await (await slide.export({ format: "layout" })).text(), "utf8");
}
await writeBlob(`${qaDir}/final-montage.webp`, await presentation.export({ format: "webp", montage: true, scale: 1 }));
const inspection = await presentation.inspect({ kind: "slide,textbox,shape,image,notes,layout", maxChars: 100000 });
await fs.writeFile(`${qaDir}/final-inspect.ndjson`, inspection.ndjson, "utf8");

const pptx = await PresentationFile.exportPptx(presentation);
await pptx.save(finalPptx);
