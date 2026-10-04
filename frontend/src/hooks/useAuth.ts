import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { changePassword, getCurrentUser, login, logout } from "../api/auth";
import { ChangePasswordData, LoginCredentials, User } from "../types/auth";
import { ApiError } from "../types/api";

export const USER_QUERY_KEY = ["currentUser"];

export function useAuth() {
  const queryClient = useQueryClient();
  const navigate = useNavigate();

  // Query current authenticated user
  const {
    data: user,
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery<User, ApiError>({
    queryKey: USER_QUERY_KEY,
    queryFn: getCurrentUser,
    retry: false, // Don't retry on 401
    staleTime: 5 * 60 * 1000,
  });

  const isAuthenticated = !!user && !isError;

  // Login mutation
  const loginMutation = useMutation<any, ApiError, LoginCredentials>({
    mutationFn: login,
    onSuccess: (data) => {
      queryClient.setQueryData(USER_QUERY_KEY, data.user);
      navigate("/", { replace: true });
    },
  });

  // Logout mutation
  const logoutMutation = useMutation<any, ApiError, void>({
    mutationFn: logout,
    onSuccess: () => {
      queryClient.clear();
      navigate("/login", { replace: true });
    },
  });

  // Change password mutation
  const changePasswordMutation = useMutation<any, ApiError, ChangePasswordData>(
    {
      mutationFn: changePassword,
    },
  );

  return {
    user,
    isAuthenticated,
    isLoading,
    isError,
    error,
    refetchUser: refetch,
    login: loginMutation.mutateAsync,
    resetLogin: loginMutation.reset,
    isLoggingIn: loginMutation.isPending,
    loginError: loginMutation.error,
    logout: logoutMutation.mutateAsync,
    isLoggingOut: logoutMutation.isPending,
    changePassword: changePasswordMutation.mutateAsync,
    isChangingPassword: changePasswordMutation.isPending,
  };
}
