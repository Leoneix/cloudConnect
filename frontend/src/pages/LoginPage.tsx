import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Cloud, Lock, User as UserIcon } from "lucide-react";
import { useAuth } from "../hooks/useAuth";
import { Button } from "../components/common/Button";
import { ErrorMessage } from "../components/common/ErrorMessage";
import styles from "./LoginPage.module.css";

export const LoginPage: React.FC = () => {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const { login, resetLogin, isLoggingIn, loginError, isAuthenticated } =
    useAuth();
  const navigate = useNavigate();

  // If already authenticated, navigate to dashboard immediately
  useEffect(() => {
    if (isAuthenticated) {
      navigate("/", { replace: true });
    }
  }, [isAuthenticated, navigate]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (isLoggingIn || !username.trim() || !password) return;

    resetLogin();

    try {
      await login({ username: username.trim(), password });
    } catch {
      // Handled via loginError state from TanStack Query hook
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.card}>
        {/* Brand Header */}
        <div className={styles.brandHeader}>
          <div className={styles.logoCircle}>
            <Cloud size={32} />
          </div>
          <h1 className={styles.title}>MyCloud</h1>
          <p className={styles.subtitle}>Your personal cloud storage</p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className={styles.form}>
          {loginError && (
            <ErrorMessage
              message={
                loginError.error?.message ||
                "Invalid username or password. Please try again."
              }
              code={loginError.error?.code}
            />
          )}

          <div className={styles.formGroup}>
            <label htmlFor="username" className={styles.label}>
              Username or Email
            </label>
            <div className={styles.inputWrapper}>
              <UserIcon size={18} className={styles.inputIcon} />
              <input
                id="username"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Enter username or email"
                autoComplete="username"
                required
                autoFocus
                disabled={isLoggingIn}
                className={styles.inputWithIcon}
              />
            </div>
          </div>

          <div className={styles.formGroup}>
            <label htmlFor="password" className={styles.label}>
              Password
            </label>
            <div className={styles.inputWrapper}>
              <Lock size={18} className={styles.inputIcon} />
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter password"
                autoComplete="current-password"
                required
                disabled={isLoggingIn}
                className={styles.inputWithIcon}
              />
            </div>
          </div>

          <Button
            type="submit"
            variant="primary"
            size="lg"
            isLoading={isLoggingIn}
            className={styles.submitBtn}
          >
            Sign In
          </Button>
        </form>

        <div className={styles.footerNote}>
          <p>Self-hosted & encrypted on your private device.</p>
        </div>
      </div>
    </div>
  );
};
