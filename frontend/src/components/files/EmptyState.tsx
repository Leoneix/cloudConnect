import React from "react";
import { FolderPlus, Upload, FolderOpen } from "lucide-react";
import { Button } from "../common/Button";
import styles from "./EmptyState.module.css";

interface EmptyStateProps {
  onUploadClick: () => void;
  onCreateFolderClick: () => void;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  onUploadClick,
  onCreateFolderClick,
}) => {
  return (
    <div className={styles.emptyContainer}>
      <div className={styles.iconCircle}>
        <FolderOpen size={40} className={styles.icon} />
      </div>
      <h3 className={styles.title}>Nothing here yet</h3>
      <p className={styles.description}>
        Upload a file or create a new folder to get started organizing your
        personal cloud.
      </p>
      <div className={styles.actions}>
        <Button
          variant="secondary"
          leftIcon={<FolderPlus size={16} />}
          onClick={onCreateFolderClick}
        >
          New Folder
        </Button>
        <Button
          variant="primary"
          leftIcon={<Upload size={16} />}
          onClick={onUploadClick}
        >
          Upload Files
        </Button>
      </div>
    </div>
  );
};
