import { apiClient } from "./api-client";

export const testingService = {
  summary: (projectId?:string) => apiClient.get("/testing/summary",{params:projectId?{project_id:projectId}:undefined}).then(response => response.data),
  modelEvaluation: () => apiClient.get("/testing/model-evaluation").then(response => response.data),
  uatSummary: (projectId?:string) => apiClient.get("/testing/uat/summary",{params:projectId?{project_id:projectId}:undefined}).then(response => response.data),
  run: (strategy:string,projectId:string) => apiClient.post(`/testing/run/${strategy}`,null,{params:{project_id:projectId}}).then(response => response.data),
};
