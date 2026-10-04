import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  createFolder,
  deleteFolder,
  getFolderContents,
  renameFolder,
} from "../api/folders";
import {
  FolderContentsResponse,
  FolderCreateRequest,
  FolderItem,
} from "../types/folder";
import { ApiError, MessageResponse } from "../types/api";

export const FOLDERS_QUERY_KEY = ["folderContents"];

export function useFolders(folderId?: number | null) {
  const queryClient = useQueryClient();
  const currentKey = [...FOLDERS_QUERY_KEY, folderId ?? "root"];

  // Query folder contents (folder metadata, subfolders, files)
  const { data, isLoading, isError, error, refetch } = useQuery<
    FolderContentsResponse,
    ApiError
  >({
    queryKey: currentKey,
    queryFn: () => getFolderContents(folderId),
  });

  // Create folder mutation
  const createFolderMutation = useMutation<
    FolderItem,
    ApiError,
    FolderCreateRequest
  >({
    mutationFn: createFolder,
    onSuccess: () => {
      // Invalidate current folder query and root query
      queryClient.invalidateQueries({ queryKey: FOLDERS_QUERY_KEY });
    },
  });

  // Rename folder mutation
  const renameFolderMutation = useMutation<
    FolderItem,
    ApiError,
    { folderId: number; name: string }
  >({
    mutationFn: ({ folderId: fId, name }) => renameFolder(fId, name),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: FOLDERS_QUERY_KEY });
    },
  });

  // Delete folder mutation
  const deleteFolderMutation = useMutation<MessageResponse, ApiError, number>({
    mutationFn: deleteFolder,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: FOLDERS_QUERY_KEY });
      queryClient.invalidateQueries({ queryKey: ["storage"] });
    },
  });

  return {
    folder: data?.folder,
    subfolders: data?.subfolders || [],
    files: data?.files || [],
    isLoading,
    isError,
    error,
    refetch,
    createFolder: createFolderMutation.mutateAsync,
    isCreatingFolder: createFolderMutation.isPending,
    createFolderError: createFolderMutation.error,
    renameFolder: renameFolderMutation.mutateAsync,
    isRenamingFolder: renameFolderMutation.isPending,
    deleteFolder: deleteFolderMutation.mutateAsync,
    isDeletingFolder: deleteFolderMutation.isPending,
  };
}
