import React from "react";
import { FolderItem } from "../../types/folder";
import { FileItem } from "../../types/file";
import { getFileIconMeta } from "../../utils/fileIcons";
import { formatFileSize } from "../../utils/formatFileSize";
import { formatDate } from "../../utils/formatDate";
import { FileActions } from "./FileActions";
import styles from "./FileRow.module.css";

interface FileRowProps {
  item: {
    type: "folder" | "file";
    data: FolderItem | FileItem;
  };
  onFolderClick?: (folderId: number) => void;
  onDownloadFile?: (file: FileItem) => void;
  onRename: (type: "folder" | "file", item: FolderItem | FileItem) => void;
  onDelete: (type: "folder" | "file", item: FolderItem | FileItem) => void;
}

export const FileRow: React.FC<FileRowProps> = ({
  item,
  onFolderClick,
  onDownloadFile,
  onRename,
  onDelete,
}) => {
  const isFolder = item.type === "folder";
  const { name, updated_at } = item.data;
  const size = !isFolder ? (item.data as FileItem).size : undefined;
  const mimeType = !isFolder ? (item.data as FileItem).mime_type : undefined;

  const iconMeta = getFileIconMeta(name, mimeType, isFolder);
  const IconComponent = iconMeta.icon;

  const handleRowClick = () => {
    if (isFolder && onFolderClick) {
      onFolderClick(item.data.id);
    } else if (!isFolder && onDownloadFile) {
      onDownloadFile(item.data as FileItem);
    }
  };

  return (
    <div
      className={`${styles.row} ${isFolder ? styles.folderRow : styles.fileRow}`}
      onClick={handleRowClick}
      role="row"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          handleRowClick();
        }
      }}
    >
      {/* Name and Icon column */}
      <div className={styles.nameCol}>
        <div
          className={styles.iconWrap}
          style={{ backgroundColor: iconMeta.bgColor, color: iconMeta.color }}
        >
          <IconComponent size={20} />
        </div>
        <span className={styles.name} title={name}>
          {name}
        </span>
      </div>

      {/* Size column */}
      <div className={styles.sizeCol}>
        {isFolder ? "—" : formatFileSize(size)}
      </div>

      {/* Modified Date column */}
      <div className={styles.dateCol}>{formatDate(updated_at)}</div>

      {/* Actions column */}
      <div className={styles.actionsCol} onClick={(e) => e.stopPropagation()}>
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
  );
};
