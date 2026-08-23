import { apiClient } from "./api-client";

export const pricingService = {
  list: () => apiClient.get("/pricing").then(r => r.data),
};
