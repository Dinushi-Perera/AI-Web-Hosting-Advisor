import { apiClient } from "./api-client";

export const testingService = {
  summary: () => apiClient.get("/testing/summary").then(response => response.data),
  modelEvaluation: () => apiClient.get("/testing/model-evaluation").then(response => response.data),
  uatSummary: () => apiClient.get("/testing/uat/summary").then(response => response.data),
};
