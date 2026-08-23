import { apiClient } from "./api-client";

export const projectDataService={
  technology:(id:string)=>apiClient.get(`/projects/${id}/technology`).then(r=>r.data),
  performance:(id:string)=>apiClient.get(`/projects/${id}/performance`).then(r=>r.data),
  performanceHistory:(id:string)=>apiClient.get(`/projects/${id}/performance/history`).then(r=>r.data),
  workload:(id:string)=>apiClient.get(`/projects/${id}/workload`).then(r=>r.data),
  recommendation:(id:string)=>apiClient.get(`/projects/${id}/recommendation`).then(r=>r.data),
  recalculate:(id:string)=>apiClient.post(`/projects/${id}/recommendation/recalculate`).then(r=>r.data),
  optimizations:(id:string)=>apiClient.get(`/projects/${id}/optimizations`).then(r=>r.data),
  updateOptimization:(id:string,status:string)=>apiClient.patch(`/optimizations/${id}/status`,{status}).then(r=>r.data),
  history:(id:string)=>apiClient.get(`/projects/${id}/history`).then(r=>r.data),
  createLoadTest:(id:string,payload:unknown)=>apiClient.post(`/projects/${id}/load-test-plan`,payload).then(r=>r.data),
  downloadLoadTest:(planId:string)=>apiClient.get(`/load-test-plans/${planId}/download`,{responseType:"blob"}).then(r=>r.data as Blob),
};
