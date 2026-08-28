import { apiClient } from "./api-client";
import type { User } from "@/types/domain";

export type UserPreferences = {
  theme: "light" | "dark" | "system";
  currency: "USD";
  timezone: string;
  chartAnimations: boolean;
  emailNotifications: boolean;
  analysisNotifications: boolean;
  onboardingCompleted: boolean;
};

export type UserSession = { id: string; device: string; browser: string; ip?: string; lastActive: string; current: boolean };

export const userService = {
  me: () => apiClient.get<User>("/users/me").then((r) => r.data),
  update: (payload: Partial<User>) => apiClient.patch<User>("/users/me", payload).then((r) => r.data),
  preferences: () => apiClient.get<UserPreferences>("/users/me/preferences").then((r) => r.data),
  updatePreferences: (payload: Partial<UserPreferences>) => apiClient.patch<UserPreferences>("/users/me/preferences", payload).then((r) => r.data),
  uploadAvatar: (file: File) => {
    const data = new FormData(); data.append("file", file);
    return apiClient.post("/users/me/avatar", data, { headers: { "Content-Type": "multipart/form-data" } }).then((r) => r.data);
  },
  removeAvatar: () => apiClient.delete("/users/me/avatar").then((r) => r.data),
  avatarUrl: () => `${apiClient.defaults.baseURL}/users/me/avatar`,
  sessions: () => apiClient.get<UserSession[]>("/users/me/sessions").then((r) => r.data),
  revokeSession: (id: string) => apiClient.delete(`/users/me/sessions/${id}`).then((r) => r.data),
  revokeAllSessions: () => apiClient.delete("/users/me/sessions").then((r) => r.data),
  changePassword: (currentPassword: string, newPassword: string) => apiClient.post("/auth/change-password", { currentPassword, newPassword }).then((r) => r.data),
};
