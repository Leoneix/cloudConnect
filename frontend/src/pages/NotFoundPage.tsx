import React from "react";
import { Link } from "react-router-dom";
import { FileQuestion, Home } from "lucide-react";
import { Button } from "../components/common/Button";
import styles from "./NotFoundPage.module.css";

export const NotFoundPage: React.FC = () => {
  return (
    <div className={styles.container}>
      <div className={styles.iconCircle}>
        <FileQuestion size={48} />
      </div>
      <h1 className={styles.code}>404</h1>
      <h2 className={styles.title}>Page not found</h2>
      <p className={styles.description}>
        The page or file location you are looking for does not exist or has been
        moved.
      </p>
      <Link to="/">
        <Button variant="primary" leftIcon={<Home size={16} />}>
          Back to My Files
        </Button>
      </Link>
    </div>
  );
};
