import { apiClient, normalizeApiError } from "./client";
import { StorageStats } from "../types/system";

export async function getStorageStats(): Promise<StorageStats> {
  try {
    const response = await apiClient.get("/system/storage");
    return response.data;
  } catch (error) {
    throw normalizeApiError(error);
  }
}
