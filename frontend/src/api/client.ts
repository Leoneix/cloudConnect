import axios from "axios";
import { ApiError } from "../types/api";

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

export const apiClient = axios.create({
  baseURL: `${apiBaseUrl.replace(/\/$/, "")}/api/v1`,
  withCredentials: true,
});

export function normalizeApiError(error: any): ApiError {
  const responseData = error?.response?.data;

  if (
    responseData &&
    typeof responseData === "object" &&
    "error" in responseData
  ) {
    return responseData as ApiError;
  }

  const message = error?.message || "Request failed.";

  return {
    error: {
      code: "REQUEST_FAILED",
      message,
    },
  };
}
