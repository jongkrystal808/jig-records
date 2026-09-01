import fs from "node:fs/promises";
import { FileBlob, PresentationFile } from "@oai/artifact-tool";

const source = "C:/Users/user/PycharmProjects/jig-record/artifacts/.presentation-edit-2pages/source.pptx";
const outDir = "C:/Users/user/PycharmProjects/jig-record/artifacts/.presentation-edit-2pages/source-inspect";

async function writeBlob(path, blob) {
  await fs.writeFile(path, new Uint8Array(await blob.arrayBuffer()));
}

const presentation = await PresentationFile.importPptx(await FileBlob.load(source));
await fs.mkdir(outDir, { recursive: true });
const snapshot = await presentation.inspect({
  kind: "slide,textbox,shape,image,table,chart,notes,thread,layout",
  include: "id,slide,name,title,text,textPreview,textChars,textLines,bbox,bboxUnit,alt,isPlaceholder,placeholders",
  maxChars: 100000,
});
await fs.writeFile(`${outDir}/template-inspect.ndjson`, snapshot.ndjson, "utf8");

for (let i = 0; i < presentation.slides.items.length; i += 1) {
  const slide = presentation.slides.items[i];
  await writeBlob(`${outDir}/slide-${i + 1}.png`, await presentation.export({ slide, format: "png", scale: 1 }));
  await fs.writeFile(`${outDir}/slide-${i + 1}.layout.json`, await (await slide.export({ format: "layout" })).text(), "utf8");
}
await writeBlob(`${outDir}/contact-sheet.webp`, await presentation.export({ format: "webp", montage: true, scale: 1 }));

const manifest = {
  source,
  slideCount: presentation.slides.items.length,
  masters: presentation.masters.items.map((m) => ({ id: m.id, name: m.name, placeholders: m.placeholders.summary() })),
  layouts: presentation.layouts.items.map((l) => ({ id: l.id, name: l.name, parentLayoutId: l.parentLayoutId, placeholders: l.placeholders.summary() })),
};
await fs.writeFile(`${outDir}/template-manifest.json`, JSON.stringify(manifest, null, 2), "utf8");
