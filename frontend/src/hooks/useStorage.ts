import { useQuery } from "@tanstack/react-query";
import { getStorageStats } from "../api/system";
import { StorageStats } from "../types/system";
import { ApiError } from "../types/api";

export const STORAGE_QUERY_KEY = ["storage"];

export function useStorage() {
  const {
    data: storage,
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery<StorageStats, ApiError>({
    queryKey: STORAGE_QUERY_KEY,
    queryFn: getStorageStats,
    staleTime: 60 * 1000,
  });

  return {
    storage,
    isLoading,
    isError,
    error,
    refetchStorage: refetch,
  };
}
