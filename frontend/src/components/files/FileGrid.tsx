import React from "react";
import { FolderItem } from "../../types/folder";
import { FileItem } from "../../types/file";
import { getFileIconMeta } from "../../utils/fileIcons";
import { formatFileSize } from "../../utils/formatFileSize";
import { FileActions } from "./FileActions";
import styles from "./FileGrid.module.css";

interface FileGridProps {
  items: Array<{
    type: "folder" | "file";
    data: FolderItem | FileItem;
  }>;
  onFolderClick?: (folderId: number) => void;
  onDownloadFile?: (file: FileItem) => void;
  onRename: (type: "folder" | "file", item: FolderItem | FileItem) => void;
  onDelete: (type: "folder" | "file", item: FolderItem | FileItem) => void;
}

export const FileGrid: React.FC<FileGridProps> = ({
  items,
  onFolderClick,
  onDownloadFile,
  onRename,
  onDelete,
}) => {
  return (
    <div className={styles.grid}>
      {items.map((item) => {
        const isFolder = item.type === "folder";
        const { id, name } = item.data;
        const size = !isFolder ? (item.data as FileItem).size : undefined;
        const mimeType = !isFolder
          ? (item.data as FileItem).mime_type
          : undefined;

        const iconMeta = getFileIconMeta(name, mimeType, isFolder);
        const IconComponent = iconMeta.icon;

        const handleCardClick = () => {
          if (isFolder && onFolderClick) {
            onFolderClick(id);
          } else if (!isFolder && onDownloadFile) {
            onDownloadFile(item.data as FileItem);
          }
        };

        return (
          <div
            key={`${item.type}-${id}`}
            className={styles.card}
            onClick={handleCardClick}
            role="button"
            tabIndex={0}
            onKeyDown={(e) => {
              if (e.key === "Enter" || e.key === " ") {
                handleCardClick();
              }
            }}
          >
            <div className={styles.cardHeader}>
              <div
                className={styles.iconWrap}
                style={{
                  backgroundColor: iconMeta.bgColor,
                  color: iconMeta.color,
                }}
              >
                <IconComponent size={24} />
              </div>
              <div onClick={(e) => e.stopPropagation()}>
                <FileActions
                  isFile={!isFolder}
                  onDownload={
                    !isFolder && onDownloadFile
                      ? () => onDownloadFile(item.data as FileItem)
                      : undefined
                  }
                  onRename={() => onRename(item.type, item.data)}
                  onDelete={() => onDelete(item.type, item.data)}
                />
              </div>
            </div>

            <div className={styles.cardBody}>
              <p className={styles.name} title={name}>
                {name}
              </p>
              <p className={styles.meta}>
                {isFolder ? "Folder" : formatFileSize(size)}
              </p>
            </div>
          </div>
        );
      })}
    </div>
  );
};
