import {
  Archive,
  File,
  FileAudio,
  FileCode,
  FileImage,
  FileSpreadsheet,
  FileText,
  FileVideo,
  Folder,
  LucideIcon,
} from "lucide-react";

export interface FileIconMeta {
  icon: LucideIcon;
  color: string;
  bgColor: string;
  label: string;
}

/**
 * Determine icon and color based on filename and mime-type.
 */
export function getFileIconMeta(
  filename: string,
  mimeType?: string | null,
  isFolder = false,
): FileIconMeta {
  if (isFolder) {
    return {
      icon: Folder,
      color: "#0284c7",
      bgColor: "#e0f2fe",
      label: "Folder",
    };
  }

  const ext = filename.split(".").pop()?.toLowerCase() || "";
  const mime = (mimeType || "").toLowerCase();

  // PDF
  if (ext === "pdf" || mime.includes("pdf")) {
    return {
      icon: FileText,
      color: "#ef4444",
      bgColor: "#fee2e2",
      label: "PDF",
    };
  }

  // Images
  if (
    ["jpg", "jpeg", "png", "gif", "webp", "svg", "bmp", "ico", "avif"].includes(
      ext,
    ) ||
    mime.startsWith("image/")
  ) {
    return {
      icon: FileImage,
      color: "#10b981",
      bgColor: "#d1fae5",
      label: "Image",
    };
  }

  // Videos
  if (
    ["mp4", "mkv", "avi", "mov", "webm", "flv", "wmv"].includes(ext) ||
    mime.startsWith("video/")
  ) {
    return {
      icon: FileVideo,
      color: "#8b5cf6",
      bgColor: "#ede9fe",
      label: "Video",
    };
  }

  // Audio
  if (
    ["mp3", "wav", "flac", "ogg", "aac", "m4a", "wma"].includes(ext) ||
    mime.startsWith("audio/")
  ) {
    return {
      icon: FileAudio,
      color: "#ec4899",
      bgColor: "#fce7f3",
      label: "Audio",
    };
  }

  // Spreadsheets / Data
  if (
    ["xls", "xlsx", "csv", "tsv"].includes(ext) ||
    mime.includes("spreadsheet") ||
    mime.includes("excel") ||
    mime === "text/csv"
  ) {
    return {
      icon: FileSpreadsheet,
      color: "#059669",
      bgColor: "#d1fae5",
      label: "Spreadsheet",
    };
  }

  // Archives
  if (
    ["zip", "tar", "gz", "7z", "rar", "bz2", "xz", "iso"].includes(ext) ||
    mime.includes("zip") ||
    mime.includes("tar") ||
    mime.includes("compressed")
  ) {
    return {
      icon: Archive,
      color: "#f59e0b",
      bgColor: "#fef3c7",
      label: "Archive",
    };
  }

  // Code / Markup
  if (
    [
      "js",
      "jsx",
      "ts",
      "tsx",
      "py",
      "html",
      "css",
      "json",
      "yaml",
      "yml",
      "sql",
      "sh",
      "bat",
      "ps1",
      "c",
      "cpp",
      "rs",
      "go",
      "java",
    ].includes(ext) ||
    mime.includes("json") ||
    mime.includes("javascript") ||
    mime.includes("html")
  ) {
    return {
      icon: FileCode,
      color: "#6366f1",
      bgColor: "#e0e7ff",
      label: "Code",
    };
  }

  // Documents / Text
  if (
    ["doc", "docx", "txt", "rtf", "odt", "md"].includes(ext) ||
    mime.startsWith("text/")
  ) {
    return {
      icon: FileText,
      color: "#0284c7",
      bgColor: "#e0f2fe",
      label: "Document",
    };
  }

  // Default Generic
  return {
    icon: File,
    color: "#64748b",
    bgColor: "#f1f5f9",
    label: "File",
  };
}
