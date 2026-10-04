import React from "react";
import {
  CheckCircle2,
  AlertCircle,
  Loader2,
  File as FileIcon,
} from "lucide-react";
import { UploadQueueItem } from "../../types/file";
import { formatFileSize } from "../../utils/formatFileSize";
import styles from "./UploadProgress.module.css";

interface UploadProgressProps {
  items: UploadQueueItem[];
}

export const UploadProgress: React.FC<UploadProgressProps> = ({ items }) => {
  return (
    <div className={styles.container}>
      {items.map((item) => {
        return (
          <div key={item.id} className={styles.itemCard}>
            <div className={styles.itemHeader}>
              <div className={styles.fileInfo}>
                <div className={styles.fileIcon}>
                  <FileIcon size={16} />
                </div>
                <div className={styles.nameBlock}>
                  <span className={styles.fileName} title={item.name}>
                    {item.name}
                  </span>
                  <span className={styles.fileSize}>
                    {formatFileSize(item.size)}
                  </span>
                </div>
              </div>

              {/* Status Badge */}
              <div className={styles.statusWrap}>
                {item.status === "uploading" && (
                  <span className={`${styles.badge} ${styles.badgeUploading}`}>
                    <Loader2 size={12} className={styles.spin} />
                    {item.progress}%
                  </span>
                )}
                {item.status === "completed" && (
                  <span className={`${styles.badge} ${styles.badgeCompleted}`}>
                    <CheckCircle2 size={12} />
                    Done
                  </span>
                )}
                {item.status === "failed" && (
                  <span className={`${styles.badge} ${styles.badgeFailed}`}>
                    <AlertCircle size={12} />
                    Failed
                  </span>
                )}
                {item.status === "waiting" && (
                  <span className={`${styles.badge} ${styles.badgeWaiting}`}>
                    Waiting
                  </span>
                )}
              </div>
            </div>

            {/* Progress Bar */}
            {item.status === "uploading" && (
              <div className={styles.progressBarBg}>
                <div
                  className={styles.progressBarFill}
                  style={{ width: `${item.progress}%` }}
                />
              </div>
            )}

            {/* Error detail */}
            {item.status === "failed" && item.errorMessage && (
              <p className={styles.errorText}>{item.errorMessage}</p>
            )}
          </div>
        );
      })}
    </div>
  );
};
