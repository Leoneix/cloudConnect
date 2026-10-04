import React from "react";
import { AlertCircle } from "lucide-react";
import styles from "./ErrorMessage.module.css";

interface ErrorMessageProps {
  message?: string | null;
  code?: string | null;
  className?: string;
}

export const ErrorMessage: React.FC<ErrorMessageProps> = ({
  message,
  code,
  className = "",
}) => {
  if (!message) return null;

  return (
    <div className={`${styles.alert} ${className}`} role="alert">
      <AlertCircle className={styles.icon} size={18} />
      <div className={styles.content}>
        <p className={styles.message}>{message}</p>
        {code && <span className={styles.code}>Error code: {code}</span>}
      </div>
    </div>
  );
};
