import React from "react";
import { Modal } from "./Modal";
import { Button } from "./Button";
import { AlertTriangle } from "lucide-react";

interface ConfirmDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  message: string;
  confirmLabel?: string;
  cancelLabel?: string;
  variant?: "danger" | "primary";
  isLoading?: boolean;
}

export const ConfirmDialog: React.FC<ConfirmDialogProps> = ({
  isOpen,
  onClose,
  onConfirm,
  title,
  message,
  confirmLabel = "Confirm",
  cancelLabel = "Cancel",
  variant = "danger",
  isLoading = false,
}) => {
  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={title}
      maxWidth="sm"
      footer={
        <>
          <Button variant="secondary" onClick={onClose} disabled={isLoading}>
            {cancelLabel}
          </Button>
          <Button variant={variant} onClick={onConfirm} isLoading={isLoading}>
            {confirmLabel}
          </Button>
        </>
      }
    >
      <div style={{ display: "flex", gap: "1rem", alignItems: "flex-start" }}>
        <div
          style={{
            backgroundColor:
              variant === "danger"
                ? "var(--danger-light)"
                : "var(--accent-light)",
            padding: "0.5rem",
            borderRadius: "var(--radius-full)",
            color:
              variant === "danger"
                ? "var(--danger-primary)"
                : "var(--accent-primary)",
            flexShrink: 0,
          }}
        >
          <AlertTriangle size={24} />
        </div>
        <p
          style={{
            color: "var(--text-secondary)",
            fontSize: "var(--font-size-sm)",
            lineHeight: 1.5,
          }}
        >
          {message}
        </p>
      </div>
    </Modal>
  );
};
