import React from "react";
import { Link } from "react-router-dom";
import { ChevronRight, Home } from "lucide-react";
import { FolderItem } from "../../types/folder";
import styles from "./Breadcrumbs.module.css";

interface BreadcrumbsProps {
  currentFolder?: FolderItem | null;
}

export const Breadcrumbs: React.FC<BreadcrumbsProps> = ({ currentFolder }) => {
  return (
    <nav
      className={styles.breadcrumbs}
      aria-label="Folder Breadcrumb Navigation"
    >
      <Link to="/" className={styles.crumb}>
        <Home size={16} />
        <span>My Files</span>
      </Link>

      {currentFolder && (
        <>
          <ChevronRight size={14} className={styles.separator} />
          <span
            className={`${styles.crumb} ${styles.current}`}
            aria-current="page"
          >
            {currentFolder.name}
          </span>
        </>
      )}
    </nav>
  );
};
