import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  deleteFile,
  downloadFile,
  getFiles,
  renameFile,
  rescanStorage,
  uploadFile,
} from "../api/files";
import { FileItem, FileListResponse } from "../types/file";
import { ApiError, MessageResponse } from "../types/api";
import { FOLDERS_QUERY_KEY } from "./useFolders";
import { STORAGE_QUERY_KEY } from "./useStorage";

export const FILES_QUERY_KEY = ["files"];

export function useFiles(folderId?: number | null) {
  const queryClient = useQueryClient();

  // Query files
  const { data, isLoading, isError, error, refetch } = useQuery<
    FileListResponse,
    ApiError
  >({
    queryKey: [...FILES_QUERY_KEY, folderId ?? "root"],
    queryFn: () => getFiles(folderId),
  });

  // Upload file mutation
  const uploadMutation = useMutation<
    FileItem,
    ApiError,
    {
      file: File;
      folderId?: number | null;
      onProgress?: (percent: number, loaded: number, total: number) => void;
    }
  >({
    mutationFn: ({ file, folderId: fId, onProgress }) =>
      uploadFile(file, fId, onProgress),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: FOLDERS_QUERY_KEY });
      queryClient.invalidateQueries({ queryKey: FILES_QUERY_KEY });
      queryClient.invalidateQueries({ queryKey: STORAGE_QUERY_KEY });
    },
  });

  // Rename file mutation
  const renameMutation = useMutation<
    FileItem,
    ApiError,
    { fileId: number; name: string }
  >({
    mutationFn: ({ fileId, name }) => renameFile(fileId, name),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: FOLDERS_QUERY_KEY });
      queryClient.invalidateQueries({ queryKey: FILES_QUERY_KEY });
    },
  });

  // Delete file mutation
  const deleteMutation = useMutation<MessageResponse, ApiError, number>({
    mutationFn: (fileId) => deleteFile(fileId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: FOLDERS_QUERY_KEY });
      queryClient.invalidateQueries({ queryKey: FILES_QUERY_KEY });
      queryClient.invalidateQueries({ queryKey: STORAGE_QUERY_KEY });
    },
  });

  const rescanMutation = useMutation<MessageResponse, ApiError, void>({
    mutationFn: () => rescanStorage(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: FOLDERS_QUERY_KEY });
      queryClient.invalidateQueries({ queryKey: FILES_QUERY_KEY });
      queryClient.invalidateQueries({ queryKey: STORAGE_QUERY_KEY });
    },
  });

  return {
    files: data?.files || [],
    total: data?.total || 0,
    isLoading,
    isError,
    error,
    refetch,
    uploadFile: uploadMutation.mutateAsync,
    isUploading: uploadMutation.isPending,
    uploadError: uploadMutation.error,
    renameFile: renameMutation.mutateAsync,
    isRenaming: renameMutation.isPending,
    deleteFile: deleteMutation.mutateAsync,
    isDeleting: deleteMutation.isPending,
    downloadFile,
    rescanStorage: rescanMutation.mutateAsync,
    isRescanning: rescanMutation.isPending,
  };
}
