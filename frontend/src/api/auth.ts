import { apiClient, normalizeApiError } from "./client";
import {
  AuthResponse,
  ChangePasswordData,
  LoginCredentials,
  User,
} from "../types/auth";

export async function login(
  credentials: LoginCredentials,
): Promise<AuthResponse> {
  try {
    const response = await apiClient.post("/auth/login", credentials);
    return response.data;
  } catch (error) {
    throw normalizeApiError(error);
  }
}

export async function logout(): Promise<{ message: string }> {
  try {
    const response = await apiClient.post("/auth/logout");
    return response.data;
  } catch (error) {
    throw normalizeApiError(error);
  }
}

export async function getCurrentUser(): Promise<User> {
  try {
    const response = await apiClient.get("/auth/me");
    return response.data;
  } catch (error) {
    throw normalizeApiError(error);
  }
}

export async function changePassword(
  data: ChangePasswordData,
): Promise<{ message: string }> {
  try {
    const response = await apiClient.post("/auth/change-password", data);
    return response.data;
  } catch (error) {
    throw normalizeApiError(error);
  }
}
