import { apiClient } from "./api-client";

export const authService = {
  login: (payload: { email: string; password: string }) => apiClient.post("/auth/login", payload).then(r => r.data),
  register: (payload: { fullName: string; email: string; password: string }) => apiClient.post("/auth/register", payload).then(r => r.data),
  logout: () => apiClient.post("/auth/logout").then(r => r.data),
  me: () => apiClient.get("/auth/me").then(r => r.data),
  forgotPassword: (email: string) => apiClient.post("/auth/forgot-password", { email }).then(r => r.data),
  resetPassword: (token: string, password: string) => apiClient.post("/auth/reset-password", { token, password }).then(r => r.data),
};
