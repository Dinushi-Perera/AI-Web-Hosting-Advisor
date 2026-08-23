import { apiClient } from "./api-client";
import type { Project } from "@/types/domain";

export const projectService = {
  list: () => apiClient.get<Project[]>("/projects").then(r => r.data),
  get: (id: string) => apiClient.get<Project>(`/projects/${id}`).then(r => r.data),
  create: (payload: unknown) => apiClient.post<Project>("/projects", payload).then(r => r.data),
  update: (id: string, payload: unknown) => apiClient.patch<Project>(`/projects/${id}`, payload).then(r => r.data),
  remove: (id: string) => apiClient.delete(`/projects/${id}`).then(r => r.data),
  duplicate: (id: string) => apiClient.post<Project>(`/projects/${id}/duplicate`).then(r => r.data),
  archive: (id: string) => apiClient.post<Project>(`/projects/${id}/archive`).then(r => r.data),
  analyse: (id: string) => apiClient.post(`/projects/${id}/analysis`).then(r => r.data),
  history: (id: string) => apiClient.get(`/projects/${id}/history`).then(r => r.data),
  createDraft: (payload: unknown) => apiClient.post<Project>("/projects/drafts", payload).then(r => r.data),
  updateDraft: (id: string, payload: unknown) => apiClient.patch<Project>(`/projects/${id}/draft`, payload).then(r => r.data),
};
