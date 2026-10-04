import { describe, it, expect } from "vitest";
import { formatFileSize } from "../utils/formatFileSize";
import { getFileIconMeta } from "../utils/fileIcons";

describe("formatFileSize", () => {
  it("formats zero bytes", () => {
    expect(formatFileSize(0)).toBe("0 B");
  });

  it("formats bytes, KB, MB, GB accurately", () => {
    expect(formatFileSize(500)).toBe("500 B");
    expect(formatFileSize(1024)).toBe("1 KB");
    expect(formatFileSize(1536)).toBe("1.5 KB");
    expect(formatFileSize(1048576)).toBe("1 MB");
    expect(formatFileSize(2516582)).toBe("2.4 MB");
    expect(formatFileSize(1073741824)).toBe("1 GB");
    expect(formatFileSize(536870912000)).toBe("500 GB");
  });

  it("handles null/undefined gracefully", () => {
    expect(formatFileSize(null)).toBe("0 B");
    expect(formatFileSize(undefined)).toBe("0 B");
  });
});

describe("getFileIconMeta", () => {
  it("identifies folders", () => {
    const meta = getFileIconMeta("University", null, true);
    expect(meta.label).toBe("Folder");
  });

  it("identifies PDF files", () => {
    const meta = getFileIconMeta("assignment.pdf", "application/pdf");
    expect(meta.label).toBe("PDF");
  });

  it("identifies Images", () => {
    const meta = getFileIconMeta("photo.jpg", "image/jpeg");
    expect(meta.label).toBe("Image");
  });

  it("identifies Code files", () => {
    const meta = getFileIconMeta("script.ts", "application/typescript");
    expect(meta.label).toBe("Code");
  });

  it("falls back to generic file icon", () => {
    const meta = getFileIconMeta("unknown.xyz", null);
    expect(meta.label).toBe("File");
  });
});
