import { apiClient } from "./api-client";

export const analysisService = {
  checkWebsite: (url: string) => apiClient.post("/analysis/check-website", { url }).then(r => r.data),
  // Local development can execute the complete pipeline eagerly, including
  // external performance checks and PDF creation, so starting an analysis
  // intentionally has a longer timeout than ordinary API requests.
  startLive: (payload: unknown) => apiClient.post("/analysis/live", payload, { timeout: 120_000 }).then(r => r.data),
  startPlanned: (payload: unknown) => apiClient.post("/analysis/planned", payload, { timeout: 120_000 }).then(r => r.data),
  startIdea: (payload: unknown) => apiClient.post("/analysis/idea", payload, { timeout: 120_000 }).then(r => r.data),
  clarifications: (payload: unknown) => apiClient.post("/analysis/clarification-questions", payload).then(r => r.data),
  status: (jobId: string) => apiClient.get(`/analysis/jobs/${jobId}`).then(r => r.data),
  cancel: (jobId: string) => apiClient.post(`/analysis/jobs/${jobId}/cancel`).then(r => r.data),
};
