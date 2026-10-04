/**
 * Format bytes into human-readable file sizes (e.g., 2.4 MB, 500 GB).
 */
export function formatFileSize(bytes: number | null | undefined): string {
  if (bytes === null || bytes === undefined || isNaN(bytes) || bytes < 0) {
    return "0 B";
  }

  if (bytes === 0) return "0 B";

  const units = ["B", "KB", "MB", "GB", "TB", "PB"];
  const k = 1024;
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  const safeI = Math.min(i, units.length - 1);

  const value = bytes / Math.pow(k, safeI);
  // If whole number, don't show decimals; otherwise show 1 decimal
  const formatted = value % 1 === 0 ? value.toString() : value.toFixed(1);

  return `${formatted} ${units[safeI]}`;
}
