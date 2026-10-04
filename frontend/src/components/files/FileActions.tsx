import React, { useState, useRef, useEffect } from "react";
import { MoreVertical, Download, Edit3, Trash2 } from "lucide-react";
import styles from "./FileActions.module.css";

interface FileActionsProps {
  isFile: boolean;
  onDownload?: () => void;
  onRename: () => void;
  onDelete: () => void;
}

export const FileActions: React.FC<FileActionsProps> = ({
  isFile,
  onDownload,
  onRename,
  onDelete,
}) => {
  const [open, setOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    if (open) {
      document.addEventListener("mousedown", handleClickOutside);
    }
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [open]);

  return (
    <div className={styles.container} ref={menuRef}>
      <button
        className={styles.menuButton}
        onClick={(e) => {
          e.stopPropagation();
          setOpen((prev) => !prev);
        }}
        aria-label="Item actions"
        aria-expanded={open}
      >
        <MoreVertical size={16} />
      </button>

      {open && (
        <div className={styles.dropdown} onClick={(e) => e.stopPropagation()}>
          {isFile && onDownload && (
            <button
              className={styles.item}
              onClick={() => {
                setOpen(false);
                onDownload();
              }}
            >
              <Download size={15} />
              <span>Download</span>
            </button>
          )}

          <button
            className={styles.item}
            onClick={() => {
              setOpen(false);
              onRename();
            }}
          >
            <Edit3 size={15} />
            <span>Rename</span>
          </button>

          <button
            className={`${styles.item} ${styles.deleteItem}`}
            onClick={() => {
              setOpen(false);
              onDelete();
            }}
          >
            <Trash2 size={15} />
            <span>Delete</span>
          </button>
        </div>
      )}
    </div>
  );
};
