import React from "react";
import { Loader2 } from "lucide-react";
import styles from "./Spinner.module.css";

interface SpinnerProps {
  size?: "sm" | "md" | "lg" | "xl";
  label?: string;
  className?: string;
}

export const Spinner: React.FC<SpinnerProps> = ({
  size = "md",
  label,
  className = "",
}) => {
  const pixelSizes = {
    sm: 16,
    md: 24,
    lg: 36,
    xl: 48,
  };

  return (
    <div
      className={`${styles.container} ${className}`}
      role="status"
      aria-live="polite"
    >
      <Loader2 size={pixelSizes[size]} className={styles.spinner} />
      {label && <p className={styles.label}>{label}</p>}
      <span className={styles.srOnly}>Loading...</span>
    </div>
  );
};
