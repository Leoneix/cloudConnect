import React, { useState } from "react";
import { Outlet } from "react-router-dom";
import { Header } from "./Header";
import { Sidebar } from "./Sidebar";
import { Modal } from "../common/Modal";
import { Button } from "../common/Button";
import { ErrorMessage } from "../common/ErrorMessage";
import { useAuth } from "../../hooks/useAuth";
import styles from "./AppLayout.module.css";

export const AppLayout: React.FC = () => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [changePasswordOpen, setChangePasswordOpen] = useState(false);
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [passwordError, setPasswordError] = useState<string | null>(null);
  const [passwordSuccess, setPasswordSuccess] = useState<string | null>(null);

  const { changePassword, isChangingPassword } = useAuth();

  const handlePasswordSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setPasswordError(null);
    setPasswordSuccess(null);

    if (!currentPassword) {
      setPasswordError("Please enter your current password.");
      return;
    }

    if (newPassword.length < 8) {
      setPasswordError("New password must be at least 8 characters long.");
      return;
    }

    if (newPassword !== confirmPassword) {
      setPasswordError("New passwords do not match.");
      return;
    }

    try {
      await changePassword({
        current_password: currentPassword,
        new_password: newPassword,
      });
      setPasswordSuccess("Password changed successfully!");
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
      setTimeout(() => {
        setChangePasswordOpen(false);
        setPasswordSuccess(null);
      }, 1500);
    } catch (err: any) {
      setPasswordError(err?.error?.message || "Failed to change password.");
    }
  };

  return (
    <div className={styles.layout}>
      <Header
        onToggleSidebar={() => setSidebarOpen((prev) => !prev)}
        onChangePasswordClick={() => setChangePasswordOpen(true)}
      />

      <div className={styles.mainContainer}>
        <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />
        <main className={styles.content}>
          <Outlet />
        </main>
      </div>

      {/* Change Password Modal */}
      <Modal
        isOpen={changePasswordOpen}
        onClose={() => setChangePasswordOpen(false)}
        title="Change Password"
        maxWidth="sm"
      >
        <form onSubmit={handlePasswordSubmit} className={styles.passwordForm}>
          {passwordError && <ErrorMessage message={passwordError} />}
          {passwordSuccess && (
            <div className={styles.successMessage} role="status">
              {passwordSuccess}
            </div>
          )}

          <div className={styles.formGroup}>
            <label htmlFor="current-pw" className={styles.label}>
              Current Password
            </label>
            <input
              id="current-pw"
              type="password"
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              placeholder="••••••••"
              required
            />
          </div>

          <div className={styles.formGroup}>
            <label htmlFor="new-pw" className={styles.label}>
              New Password
            </label>
            <input
              id="new-pw"
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              placeholder="••••••••"
              minLength={8}
              required
            />
            <span className={styles.helperText}>Minimum 8 characters</span>
          </div>

          <div className={styles.formGroup}>
            <label htmlFor="confirm-pw" className={styles.label}>
              Confirm New Password
            </label>
            <input
              id="confirm-pw"
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="••••••••"
              required
            />
          </div>

          <div className={styles.modalActions}>
            <Button
              type="button"
              variant="secondary"
              onClick={() => setChangePasswordOpen(false)}
              disabled={isChangingPassword}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              isLoading={isChangingPassword}
            >
              Save Password
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
