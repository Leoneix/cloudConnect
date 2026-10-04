import React, { useState } from "react";
import { Modal } from "../common/Modal";
import { Button } from "../common/Button";
import { ErrorMessage } from "../common/ErrorMessage";
import styles from "./CreateFolderDialog.module.css";

interface CreateFolderDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (name: string) => Promise<any>;
}

export const CreateFolderDialog: React.FC<CreateFolderDialogProps> = ({
  isOpen,
  onClose,
  onSubmit,
}) => {
  const [folderName, setFolderName] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const clean = folderName.trim();
    if (!clean) {
      setError("Folder name cannot be empty.");
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      await onSubmit(clean);
      setFolderName("");
      onClose();
    } catch (err: any) {
      setError(err?.error?.message || "Failed to create folder.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleClose = () => {
    if (!isLoading) {
      setFolderName("");
      setError(null);
      onClose();
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title="New Folder"
      maxWidth="sm"
    >
      <form onSubmit={handleSubmit} className={styles.form}>
        {error && <ErrorMessage message={error} />}

        <div className={styles.inputGroup}>
          <label htmlFor="new-folder-name" className={styles.label}>
            Folder name
          </label>
          <input
            id="new-folder-name"
            type="text"
            value={folderName}
            onChange={(e) => setFolderName(e.target.value)}
            placeholder="e.g. University, Photos, Projects"
            autoFocus
            required
            disabled={isLoading}
          />
        </div>

        <div className={styles.actions}>
          <Button
            type="button"
            variant="secondary"
            onClick={handleClose}
            disabled={isLoading}
          >
            Cancel
          </Button>
          <Button type="submit" variant="primary" isLoading={isLoading}>
            Create
          </Button>
        </div>
      </form>
    </Modal>
  );
};
