export function scrollReportResultsIntoView(target: HTMLElement | null): void {
  if (!target || typeof window === "undefined") return;
  const viewportOffset = Math.max(88, Math.min(160, window.innerHeight * 0.17));
  const targetTop = Math.max(0, window.scrollY + target.getBoundingClientRect().top - viewportOffset);
  const reduceMotion = window.matchMedia?.("(prefers-reduced-motion: reduce)").matches ?? false;
  window.scrollTo({ top: targetTop, behavior: reduceMotion ? "auto" : "smooth" });
}
