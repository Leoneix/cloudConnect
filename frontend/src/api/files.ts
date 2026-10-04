import { apiClient, normalizeApiError } from "./client";
import { FileItem, FileListResponse } from "../types/file";

export async function getFiles(
  folderId?: number | null,
): Promise<FileListResponse> {
  try {
    const response = await apiClient.get("/files", {
      params:
        folderId === null || folderId === undefined
          ? {}
          : { folder_id: folderId },
    });
    return response.data;
  } catch (error) {
    throw normalizeApiError(error);
  }
}

export async function uploadFile(
  file: File,
  folderId?: number | null,
  onProgress?: (percent: number, loaded: number, total: number) => void,
): Promise<FileItem> {
  try {
    const formData = new FormData();
    formData.append("file", file);

    if (folderId !== null && folderId !== undefined) {
      formData.append("folder_id", String(folderId));
    }

    const response = await apiClient.post("/files/upload", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
      onUploadProgress: (progressEvent) => {
        if (!onProgress || !progressEvent.total) return;

        const percent = Math.round(
          (progressEvent.loaded / progressEvent.total) * 100,
        );
        onProgress(percent, progressEvent.loaded, progressEvent.total);
      },
    });

    return response.data;
  } catch (error) {
    throw normalizeApiError(error);
  }
}

export async function downloadFile(
  fileId: number,
  fileName?: string,
): Promise<void> {
  try {
    const response = await apiClient.get(`/files/${fileId}/download`, {
      responseType: "blob",
    });

    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement("a");
    link.href = url;
    link.download = fileName || "download";
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  } catch (error) {
    throw normalizeApiError(error);
  }
}

export async function renameFile(
  fileId: number,
  name: string,
): Promise<FileItem> {
  try {
    const response = await apiClient.patch(`/files/${fileId}`, { name });
    return response.data;
  } catch (error) {
    throw normalizeApiError(error);
  }
}

export async function deleteFile(fileId: number): Promise<{ message: string }> {
  try {
    const response = await apiClient.delete(`/files/${fileId}`);
    return response.data;
  } catch (error) {
    throw normalizeApiError(error);
  }
}

export async function rescanStorage(): Promise<{ message: string }> {
  try {
    const response = await apiClient.post("/system/rescan");
    return response.data;
  } catch (error) {
    throw normalizeApiError(error);
  }
}
