export interface FileItem {
  id: number;
  name: string;
  size: number;
  mime_type?: string | null;
  extension?: string | null;
  checksum?: string | null;
  folder_id?: number | null;
  created_at: string;
  updated_at: string;
}

export interface FileListResponse {
  files: FileItem[];
  total: number;
}

export interface FileRenameRequest {
  name: string;
}

export interface UploadQueueItem {
  id: string;
  file: File;
  name: string;
  size: number;
  progress: number;
  status: "waiting" | "uploading" | "completed" | "failed" | "cancelled";
  errorMessage?: string;
}
