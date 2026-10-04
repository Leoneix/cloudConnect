import React, { useState } from "react";
import { LayoutGrid, List, RotateCcw } from "lucide-react";
import { FolderItem } from "../../types/folder";
import { FileItem } from "../../types/file";
import { FileRow } from "./FileRow";
import { FileGrid } from "./FileGrid";
import { EmptyState } from "./EmptyState";
import { Spinner } from "../common/Spinner";
import { ErrorMessage } from "../common/ErrorMessage";
import { Modal } from "../common/Modal";
import { ConfirmDialog } from "../common/ConfirmDialog";
import { Button } from "../common/Button";
import styles from "./FileBrowser.module.css";

interface FileBrowserProps {
  currentFolder?: FolderItem | null;
  subfolders: FolderItem[];
  files: FileItem[];
  isLoading: boolean;
  isError: boolean;
  errorMessage?: string | null;
  onRefresh: () => void;
  onNavigateFolder: (folderId: number) => void;
  onDownloadFile: (file: FileItem) => void;
  onRenameFolder: (folderId: number, newName: string) => Promise<any>;
  onRenameFile: (fileId: number, newName: string) => Promise<any>;
  onDeleteFolder: (folderId: number) => Promise<any>;
  onDeleteFile: (fileId: number) => Promise<any>;
  onUploadClick: () => void;
  onCreateFolderClick: () => void;
}

export const FileBrowser: React.FC<FileBrowserProps> = ({
  subfolders,
  files,
  isLoading,
  isError,
  errorMessage,
  onRefresh,
  onNavigateFolder,
  onDownloadFile,
  onRenameFolder,
  onRenameFile,
  onDeleteFolder,
  onDeleteFile,
  onUploadClick,
  onCreateFolderClick,
}) => {
  const [viewMode, setViewMode] = useState<"list" | "grid">("list");

  // Rename modal state
  const [renameTarget, setRenameTarget] = useState<{
    type: "folder" | "file";
    item: FolderItem | FileItem;
  } | null>(null);
  const [newName, setNewName] = useState("");
  const [renameLoading, setRenameLoading] = useState(false);
  const [renameError, setRenameError] = useState<string | null>(null);

  // Delete modal state
  const [deleteTarget, setDeleteTarget] = useState<{
    type: "folder" | "file";
    item: FolderItem | FileItem;
  } | null>(null);
  const [deleteLoading, setDeleteLoading] = useState(false);

  // Prepare combined items (folders first, then files)
  const combinedItems = [
    ...subfolders.map((f) => ({ type: "folder" as const, data: f })),
    ...files.map((f) => ({ type: "file" as const, data: f })),
  ];

  // Open rename modal
  const handleOpenRename = (
    type: "folder" | "file",
    item: FolderItem | FileItem,
  ) => {
    setRenameTarget({ type, item });
    setNewName(item.name);
    setRenameError(null);
  };

  // Submit rename
  const handleRenameSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!renameTarget) return;

    if (!newName.trim()) {
      setRenameError("Name cannot be empty.");
      return;
    }

    setRenameLoading(true);
    setRenameError(null);

    try {
      if (renameTarget.type === "folder") {
        await onRenameFolder(renameTarget.item.id, newName.trim());
      } else {
        await onRenameFile(renameTarget.item.id, newName.trim());
      }
      setRenameTarget(null);
    } catch (err: any) {
      setRenameError(err?.error?.message || "Failed to rename item.");
    } finally {
      setRenameLoading(false);
    }
  };

  // Open delete dialog
  const handleOpenDelete = (
    type: "folder" | "file",
    item: FolderItem | FileItem,
  ) => {
    setDeleteTarget({ type, item });
  };

  // Submit delete
  const handleDeleteConfirm = async () => {
    if (!deleteTarget) return;

    setDeleteLoading(true);
    try {
      if (deleteTarget.type === "folder") {
        await onDeleteFolder(deleteTarget.item.id);
      } else {
        await onDeleteFile(deleteTarget.item.id);
      }
      setDeleteTarget(null);
    } catch (err: any) {
      alert(err?.error?.message || "Failed to delete item.");
    } finally {
      setDeleteLoading(false);
    }
  };

  if (isLoading) {
    return (
      <div className={styles.loadingContainer}>
        <Spinner size="lg" label="Loading files and folders..." />
      </div>
    );
  }

  if (isError) {
    return (
      <div className={styles.errorContainer}>
        <ErrorMessage
          message={
            errorMessage || "Unable to load files. Check server connection."
          }
        />
        <Button
          variant="secondary"
          leftIcon={<RotateCcw size={16} />}
          onClick={onRefresh}
        >
          Try Again
        </Button>
      </div>
    );
  }

  return (
    <div className={styles.browserContainer}>
      {/* Top Toolbar (view switcher & item count) */}
      <div className={styles.toolbar}>
        <span className={styles.itemCount}>
          {combinedItems.length} {combinedItems.length === 1 ? "item" : "items"}
        </span>

        <div className={styles.viewToggle}>
          <button
            className={`${styles.toggleBtn} ${viewMode === "list" ? styles.active : ""}`}
            onClick={() => setViewMode("list")}
            aria-label="List view"
            title="List view"
          >
            <List size={18} />
          </button>
          <button
            className={`${styles.toggleBtn} ${viewMode === "grid" ? styles.active : ""}`}
            onClick={() => setViewMode("grid")}
            aria-label="Grid view"
            title="Grid view"
          >
            <LayoutGrid size={18} />
          </button>
        </div>
      </div>

      {/* Main Content: Empty State vs Items */}
      {combinedItems.length === 0 ? (
        <EmptyState
          onUploadClick={onUploadClick}
          onCreateFolderClick={onCreateFolderClick}
        />
      ) : viewMode === "list" ? (
        <div
          className={styles.tableWrapper}
          role="table"
          aria-label="Files and folders table"
        >
          {/* Table Header */}
          <div className={styles.tableHeader} role="row">
            <div className={styles.nameHeader} role="columnheader">
              Name
            </div>
            <div className={styles.sizeHeader} role="columnheader">
              Size
            </div>
            <div className={styles.dateHeader} role="columnheader">
              Modified
            </div>
            <div className={styles.actionsHeader} role="columnheader">
              <span className={styles.srOnly}>Actions</span>
            </div>
          </div>

          {/* Rows */}
          <div className={styles.tableBody} role="rowgroup">
            {combinedItems.map((item) => (
              <FileRow
                key={`${item.type}-${item.data.id}`}
                item={item}
                onFolderClick={onNavigateFolder}
                onDownloadFile={onDownloadFile}
                onRename={handleOpenRename}
                onDelete={handleOpenDelete}
              />
            ))}
          </div>
        </div>
      ) : (
        <FileGrid
          items={combinedItems}
          onFolderClick={onNavigateFolder}
          onDownloadFile={onDownloadFile}
          onRename={handleOpenRename}
          onDelete={handleOpenDelete}
        />
      )}

      {/* Rename Modal */}
      <Modal
        isOpen={!!renameTarget}
        onClose={() => setRenameTarget(null)}
        title={`Rename ${renameTarget?.type === "folder" ? "Folder" : "File"}`}
        maxWidth="sm"
      >
        <form onSubmit={handleRenameSubmit} className={styles.modalForm}>
          {renameError && <ErrorMessage message={renameError} />}

          <div className={styles.inputGroup}>
            <label htmlFor="rename-input" className={styles.inputLabel}>
              Name
            </label>
            <input
              id="rename-input"
              type="text"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              autoFocus
              required
            />
          </div>

          <div className={styles.modalActions}>
            <Button
              type="button"
              variant="secondary"
              onClick={() => setRenameTarget(null)}
              disabled={renameLoading}
            >
              Cancel
            </Button>
            <Button type="submit" variant="primary" isLoading={renameLoading}>
              Save
            </Button>
          </div>
        </form>
      </Modal>

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        isOpen={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        onConfirm={handleDeleteConfirm}
        title={`Delete "${deleteTarget?.item.name}"?`}
        message={
          deleteTarget?.type === "folder"
            ? "This will delete the folder and all files and subfolders inside it."
            : "The file will be moved to trash and removed from active storage."
        }
        confirmLabel="Delete"
        variant="danger"
        isLoading={deleteLoading}
      />
    </div>
  );
};
