import React, { useState, useRef, useEffect } from "react";
import {
  Cloud,
  Menu,
  User as UserIcon,
  LogOut,
  KeyRound,
  ChevronDown,
} from "lucide-react";
import { useAuth } from "../../hooks/useAuth";
import styles from "./Header.module.css";

interface HeaderProps {
  onToggleSidebar?: () => void;
  onChangePasswordClick?: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  onToggleSidebar,
  onChangePasswordClick,
}) => {
  const { user, logout, isLoggingOut } = useAuth();
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown on click outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node)
      ) {
        setDropdownOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <header className={styles.header}>
      <div className={styles.leftSection}>
        {onToggleSidebar && (
          <button
            className={styles.menuButton}
            onClick={onToggleSidebar}
            aria-label="Toggle navigation menu"
          >
            <Menu size={22} />
          </button>
        )}
        <div className={styles.brand}>
          <div className={styles.brandIcon}>
            <Cloud size={24} />
          </div>
          <span className={styles.brandTitle}>MyCloud</span>
        </div>
      </div>

      <div className={styles.rightSection} ref={dropdownRef}>
        <button
          className={styles.userButton}
          onClick={() => setDropdownOpen((prev) => !prev)}
          aria-expanded={dropdownOpen}
          aria-haspopup="true"
        >
          <div className={styles.avatar}>
            <UserIcon size={16} />
          </div>
          <span className={styles.username}>{user?.username || "Account"}</span>
          <ChevronDown size={14} className={styles.chevron} />
        </button>

        {dropdownOpen && (
          <div className={styles.dropdown}>
            <div className={styles.dropdownHeader}>
              <p className={styles.dropdownName}>{user?.username}</p>
              <p className={styles.dropdownEmail}>{user?.email}</p>
              <span className={styles.roleBadge}>
                {user?.role?.toUpperCase()}
              </span>
            </div>

            <div className={styles.dropdownDivider} />

            {onChangePasswordClick && (
              <button
                className={styles.dropdownItem}
                onClick={() => {
                  setDropdownOpen(false);
                  onChangePasswordClick();
                }}
              >
                <KeyRound size={16} />
                <span>Change Password</span>
              </button>
            )}

            <button
              className={`${styles.dropdownItem} ${styles.logoutItem}`}
              onClick={() => {
                setDropdownOpen(false);
                logout();
              }}
              disabled={isLoggingOut}
            >
              <LogOut size={16} />
              <span>{isLoggingOut ? "Logging out..." : "Log Out"}</span>
            </button>
          </div>
        )}
      </div>
    </header>
  );
};
