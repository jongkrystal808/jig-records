import { FileBlob, PresentationFile } from "@oai/artifact-tool";
const presentation = await PresentationFile.importPptx(await FileBlob.load("C:/Users/user/PycharmProjects/jig-record/artifacts/.presentation-edit-2pages/source.pptx"));
console.log(presentation.help("*", { search: "slide duplicate moveTo remove delete collection", include: ["index", "examples", "notes"], maxChars: 12000 }));
console.log("slides collection", Object.getOwnPropertyNames(Object.getPrototypeOf(presentation.slides)));
console.log("slide", Object.getOwnPropertyNames(Object.getPrototypeOf(presentation.slides.items[0])));
console.log("shape collection", Object.getOwnPropertyNames(Object.getPrototypeOf(presentation.slides.items[0].shapes)));
