import React from "react";
import { Link, useSearchParams } from "react-router-dom";
import { HardDrive, FolderOpen, X } from "lucide-react";
import { useStorage } from "../../hooks/useStorage";
import { formatFileSize } from "../../utils/formatFileSize";
import { Spinner } from "../common/Spinner";
import styles from "./Sidebar.module.css";

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ isOpen, onClose }) => {
  const [searchParams] = useSearchParams();
  const currentFolderId = searchParams.get("folder");
  const isRoot = !currentFolderId;
  const { storage, isLoading } = useStorage();

  return (
    <>
      {/* Mobile backdrop overlay */}
      {isOpen && (
        <div className={styles.overlay} onClick={onClose} aria-hidden="true" />
      )}

      <aside className={`${styles.sidebar} ${isOpen ? styles.open : ""}`}>
        {/* Mobile close button */}
        <div className={styles.mobileHeader}>
          <span className={styles.mobileTitle}>Navigation</span>
          <button
            className={styles.closeBtn}
            onClick={onClose}
            aria-label="Close navigation menu"
          >
            <X size={20} />
          </button>
        </div>

        {/* Navigation list */}
        <nav className={styles.nav}>
          <p className={styles.navSectionTitle}>Drive</p>
          <Link
            to="/"
            className={`${styles.navItem} ${isRoot ? styles.active : ""}`}
            onClick={onClose}
          >
            <FolderOpen size={18} className={styles.navIcon} />
            <span>My Files</span>
          </Link>
        </nav>

        {/* Storage Widget at bottom of sidebar */}
        <div className={styles.storageWidget}>
          <div className={styles.storageHeader}>
            <div className={styles.storageTitleWrap}>
              <HardDrive size={16} className={styles.storageIcon} />
              <span className={styles.storageTitle}>Storage</span>
            </div>
            {storage && (
              <span className={styles.storagePercent}>
                {storage.usage_percent.toFixed(0)}%
              </span>
            )}
          </div>

          {isLoading ? (
            <Spinner size="sm" />
          ) : storage ? (
            <>
              <div
                className={styles.progressBarBg}
                role="progressbar"
                aria-valuenow={storage.usage_percent}
                aria-valuemin={0}
                aria-valuemax={100}
              >
                <div
                  className={styles.progressBarFill}
                  style={{
                    width: `${Math.min(100, Math.max(0, storage.usage_percent))}%`,
                    backgroundColor:
                      storage.usage_percent > 90
                        ? "var(--danger-primary)"
                        : storage.usage_percent > 75
                          ? "var(--warning-primary)"
                          : "var(--accent-primary)",
                  }}
                />
              </div>

              <div className={styles.storageDetails}>
                <p className={styles.storageDetailText}>
                  {formatFileSize(storage.used_bytes)} used
                </p>
                <p className={styles.storageDetailMuted}>
                  of {formatFileSize(storage.total_bytes)}
                </p>
              </div>

              <p className={styles.storageFreeText}>
                {formatFileSize(storage.free_bytes)} free
              </p>
            </>
          ) : (
            <p className={styles.storageErrorText}>Storage info unavailable</p>
          )}
        </div>
      </aside>
    </>
  );
};
