import { apiClient, normalizeApiError } from "./client";
import {
  FolderContentsResponse,
  FolderCreateRequest,
  FolderItem,
} from "../types/folder";

export async function getFolderContents(
  folderId?: number | null,
): Promise<FolderContentsResponse> {
  try {
    const path =
      folderId === null || folderId === undefined
        ? "/folders"
        : `/folders/${folderId}`;
    const response = await apiClient.get(path);
    return response.data;
  } catch (error) {
    throw normalizeApiError(error);
  }
}

export async function createFolder(
  payload: FolderCreateRequest,
): Promise<FolderItem> {
  try {
    const response = await apiClient.post("/folders", payload);
    return response.data;
  } catch (error) {
    throw normalizeApiError(error);
  }
}

export async function renameFolder(
  folderId: number,
  name: string,
): Promise<FolderItem> {
  try {
    const response = await apiClient.patch(`/folders/${folderId}`, { name });
    return response.data;
  } catch (error) {
    throw normalizeApiError(error);
  }
}

export async function deleteFolder(
  folderId: number,
): Promise<{ message: string }> {
  try {
    const response = await apiClient.delete(`/folders/${folderId}`);
    return response.data;
  } catch (error) {
    throw normalizeApiError(error);
  }
}
