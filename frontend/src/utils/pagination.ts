export function pageAfterItemRemoval(currentPage: number, currentPageItemCount: number): number {
  if (currentPage > 1 && currentPageItemCount <= 1) return currentPage - 1;
  return Math.max(1, currentPage);
}
