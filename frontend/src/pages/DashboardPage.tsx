import React, { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { FolderPlus, RefreshCw } from "lucide-react";
import { useFolders } from "../hooks/useFolders";
import { useFiles } from "../hooks/useFiles";
import { Breadcrumbs } from "../components/files/Breadcrumbs";
import { FileBrowser } from "../components/files/FileBrowser";
import { CreateFolderDialog } from "../components/folders/CreateFolderDialog";
import { UploadButton } from "../components/upload/UploadButton";
import { UploadDialog } from "../components/upload/UploadDialog";
import { Button } from "../components/common/Button";
import { UploadQueueItem } from "../types/file";
import styles from "./DashboardPage.module.css";

export const DashboardPage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const folderParam = searchParams.get("folder");
  const currentFolderId = folderParam ? parseInt(folderParam, 10) : null;

  // Folder and file query hooks
  const {
    folder: currentFolder,
    subfolders,
    files,
    isLoading,
    isError,
    error,
    refetch,
    createFolder,
    renameFolder,
    deleteFolder,
  } = useFolders(currentFolderId);

  const {
    uploadFile,
    renameFile,
    deleteFile,
    downloadFile,
    rescanStorage,
    isRescanning,
  } = useFiles(currentFolderId);

  // Dialog states
  const [createFolderOpen, setCreateFolderOpen] = useState(false);
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false);
  const [uploadQueue, setUploadQueue] = useState<UploadQueueItem[]>([]);
  const [isUploading, setIsUploading] = useState(false);

  useEffect(() => {
    rescanStorage().catch(() => undefined);
  }, [currentFolderId, rescanStorage]);

  // Handle folder navigation
  const handleNavigateFolder = (folderId: number) => {
    setSearchParams({ folder: folderId.toString() });
  };

  // Handle files selected from file picker
  const handleFilesSelected = (files: File[]) => {
    const newItems: UploadQueueItem[] = files.map((file) => ({
      id: `${file.name}-${Date.now()}-${Math.random()}`,
      file,
      name: file.name,
      size: file.size,
      progress: 0,
      status: "waiting",
    }));

    setUploadQueue((prev) => [...prev, ...newItems]);
    setUploadDialogOpen(true);
  };

  // Start executing uploads sequentially
  const handleStartUpload = async () => {
    setIsUploading(true);

    for (let i = 0; i < uploadQueue.length; i++) {
      const item = uploadQueue[i];
      if (item.status !== "waiting" && item.status !== "failed") continue;

      // Update status to uploading
      setUploadQueue((prev) =>
        prev.map((qItem, idx) =>
          idx === i ? { ...qItem, status: "uploading", progress: 0 } : qItem,
        ),
      );

      try {
        await uploadFile({
          file: item.file,
          folderId: currentFolderId,
          onProgress: (percent) => {
            setUploadQueue((prev) =>
              prev.map((qItem, idx) =>
                idx === i ? { ...qItem, progress: percent } : qItem,
              ),
            );
          },
        });

        // Mark completed
        setUploadQueue((prev) =>
          prev.map((qItem, idx) =>
            idx === i
              ? { ...qItem, status: "completed", progress: 100 }
              : qItem,
          ),
        );
      } catch (err: any) {
        // Mark failed
        const msg = err?.error?.message || "Upload failed.";
        setUploadQueue((prev) =>
          prev.map((qItem, idx) =>
            idx === i
              ? { ...qItem, status: "failed", errorMessage: msg }
              : qItem,
          ),
        );
      }
    }

    setIsUploading(false);
  };

  const handleClearCompletedUploads = () => {
    setUploadQueue((prev) =>
      prev.filter((i) => i.status !== "completed" && i.status !== "failed"),
    );
    if (
      uploadQueue.every(
        (i) => i.status === "completed" || i.status === "failed",
      )
    ) {
      setUploadDialogOpen(false);
    }
  };

  return (
    <div className={styles.dashboard}>
      {/* Top Action Bar */}
      <div className={styles.actionBar}>
        <div className={styles.breadcrumbsWrapper}>
          <Breadcrumbs currentFolder={currentFolder} />
        </div>

        <div className={styles.actionButtons}>
          <Button
            variant="secondary"
            leftIcon={
              <RefreshCw size={16} className={isRescanning ? "spin" : ""} />
            }
            onClick={() => rescanStorage()}
            disabled={isRescanning}
          >
            {isRescanning ? "Scanning..." : "Rescan"}
          </Button>

          <Button
            variant="secondary"
            leftIcon={<FolderPlus size={16} />}
            onClick={() => setCreateFolderOpen(true)}
          >
            New Folder
          </Button>

          <UploadButton onFilesSelected={handleFilesSelected} />
        </div>
      </div>

      {/* File Browser Grid / Table */}
      <FileBrowser
        currentFolder={currentFolder}
        subfolders={subfolders}
        files={files}
        isLoading={isLoading}
        isError={isError}
        errorMessage={error?.error?.message}
        onRefresh={refetch}
        onNavigateFolder={handleNavigateFolder}
        onDownloadFile={(f) => downloadFile(f.id, f.name)}
        onRenameFolder={(id, name) => renameFolder({ folderId: id, name })}
        onRenameFile={(id, name) => renameFile({ fileId: id, name })}
        onDeleteFolder={(id) => deleteFolder(id)}
        onDeleteFile={(id) => deleteFile(id)}
        onUploadClick={() => {
          const fakeInput = document.createElement("input");
          fakeInput.type = "file";
          fakeInput.multiple = true;
          fakeInput.onchange = (e: any) => {
            if (e.target.files?.length) {
              handleFilesSelected(Array.from(e.target.files));
            }
          };
          fakeInput.click();
        }}
        onCreateFolderClick={() => setCreateFolderOpen(true)}
      />

      {/* Create Folder Modal */}
      <CreateFolderDialog
        isOpen={createFolderOpen}
        onClose={() => setCreateFolderOpen(false)}
        onSubmit={(name) => createFolder({ name, parent_id: currentFolderId })}
      />

      {/* Upload Progress Modal */}
      <UploadDialog
        isOpen={uploadDialogOpen}
        onClose={() => setUploadDialogOpen(false)}
        queue={uploadQueue}
        isUploading={isUploading}
        onStartUpload={handleStartUpload}
        onClearCompleted={handleClearCompletedUploads}
      />
    </div>
  );
};
