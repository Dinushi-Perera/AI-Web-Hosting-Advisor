import { apiClient } from "./api-client";

export const analysisService = {
  checkWebsite: (url: string) => apiClient.post("/analysis/check-website", { url }).then(r => r.data),
  startLive: (payload: unknown) => apiClient.post("/analysis/live", payload).then(r => r.data),
  startPlanned: (payload: unknown) => apiClient.post("/analysis/planned", payload).then(r => r.data),
  startIdea: (payload: unknown) => apiClient.post("/analysis/idea", payload).then(r => r.data),
  status: (jobId: string) => apiClient.get(`/analysis/jobs/${jobId}`).then(r => r.data),
  cancel: (jobId: string) => apiClient.post(`/analysis/jobs/${jobId}/cancel`).then(r => r.data),
};
