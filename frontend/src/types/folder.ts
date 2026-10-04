import { FileItem } from "./file";

export interface FolderItem {
  id: number;
  name: string;
  parent_id?: number | null;
  owner_id: number;
  created_at: string;
  updated_at: string;
}

export interface FolderCreateRequest {
  name: string;
  parent_id?: number | null;
}

export interface FolderContentsResponse {
  folder?: FolderItem | null;
  subfolders: FolderItem[];
  files: FileItem[];
}
