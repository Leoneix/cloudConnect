export interface User {
  id: number;
  username: string;
  email: string;
  role: "user" | "admin";
  is_active: boolean;
  created_at: string;
  last_login?: string | null;
}

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface ChangePasswordData {
  current_password: string;
  new_password: string;
}

export interface AuthResponse {
  user: User;
  message: string;
}
