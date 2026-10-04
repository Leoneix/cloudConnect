import React from "react";
import { Modal } from "../common/Modal";
import { Button } from "../common/Button";
import { UploadProgress } from "./UploadProgress";
import { UploadQueueItem } from "../../types/file";
import styles from "./UploadDialog.module.css";

interface UploadDialogProps {
  isOpen: boolean;
  onClose: () => void;
  queue: UploadQueueItem[];
  isUploading: boolean;
  onStartUpload: () => void;
  onClearCompleted: () => void;
}

export const UploadDialog: React.FC<UploadDialogProps> = ({
  isOpen,
  onClose,
  queue,
  isUploading,
  onStartUpload,
  onClearCompleted,
}) => {
  const hasWaiting = queue.some((i) => i.status === "waiting");
  const hasCompletedOrFailed = queue.some(
    (i) => i.status === "completed" || i.status === "failed",
  );
  const allDone =
    queue.length > 0 && queue.every((i) => i.status === "completed");

  return (
    <Modal
      isOpen={isOpen}
      onClose={isUploading ? () => {} : onClose}
      title={isUploading ? "Uploading Files..." : "Upload Queue"}
      maxWidth="md"
      footer={
        <div className={styles.footerActions}>
          {hasCompletedOrFailed && !isUploading && (
            <Button variant="ghost" size="sm" onClick={onClearCompleted}>
              Clear Finished
            </Button>
          )}

          <div className={styles.rightButtons}>
            <Button
              variant="secondary"
              onClick={onClose}
              disabled={isUploading}
            >
              {allDone ? "Close" : "Cancel"}
            </Button>

            {hasWaiting && (
              <Button
                variant="primary"
                onClick={onStartUpload}
                isLoading={isUploading}
              >
                Start Upload
              </Button>
            )}
          </div>
        </div>
      }
    >
      <div className={styles.body}>
        {queue.length === 0 ? (
          <p className={styles.emptyText}>
            No files currently queued for upload.
          </p>
        ) : (
          <UploadProgress items={queue} />
        )}
      </div>
    </Modal>
  );
};
