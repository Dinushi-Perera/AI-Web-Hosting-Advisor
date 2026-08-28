import { apiClient } from "./api-client";

export const pricingService = {
  list: () => apiClient.get("/pricing").then(r => r.data),
  compare: (architecture?:string) => apiClient.get("/pricing/compare",{params:{architecture:architecture||undefined}}).then(r=>r.data),
  projectCost: (projectId:string) => apiClient.get(`/projects/${projectId}/cost`).then(r=>r.data),
};
