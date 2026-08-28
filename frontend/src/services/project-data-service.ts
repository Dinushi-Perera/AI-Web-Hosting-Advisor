import { apiClient } from "./api-client";

export const projectDataService={
  technology:(id:string)=>apiClient.get(`/projects/${id}/technology`).then(r=>r.data),
  performance:(id:string)=>apiClient.get(`/projects/${id}/performance`).then(r=>r.data),
  performanceHistory:(id:string)=>apiClient.get(`/projects/${id}/performance/history`).then(r=>r.data),
  workload:(id:string)=>apiClient.get(`/projects/${id}/workload`).then(r=>r.data),
  recommendation:(id:string)=>apiClient.get(`/projects/${id}/recommendation`).then(r=>r.data),
  architecture:(id:string)=>apiClient.get(`/projects/${id}/architecture`).then(r=>r.data),
  analysisSummary:(id:string)=>apiClient.get(`/projects/${id}/analysis-summary`).then(r=>r.data),
  cost:(id:string)=>apiClient.get(`/projects/${id}/cost`).then(r=>r.data),
  recalculate:(id:string)=>apiClient.post(`/projects/${id}/recommendation/recalculate`).then(r=>r.data),
  optimizations:(id:string)=>apiClient.get(`/projects/${id}/optimizations`).then(r=>r.data),
  updateOptimization:(id:string,status:string)=>apiClient.patch(`/optimizations/${id}/status`,{status}).then(r=>r.data),
  history:(id:string)=>apiClient.get(`/projects/${id}/history`).then(r=>r.data),
  // A managed k6 scenario can intentionally run for up to two minutes.  Keep
  // this request alive long enough for the server to finish and save its report.
  runManagedLoadTest:(id:string,payload:unknown)=>apiClient.post(`/projects/${id}/load-test/run-managed`,payload,{timeout:180_000}).then(r=>r.data),
  loadTestRecommendation:(id:string)=>apiClient.get(`/projects/${id}/load-test/recommendation`).then(r=>r.data),
  loadTestHistory:(id:string)=>apiClient.get(`/projects/${id}/load-tests/history`).then(r=>r.data),
  compareLoadTests:(id:string,first:string,second:string)=>apiClient.get(`/projects/${id}/load-tests/compare`,{params:{first,second}}).then(r=>r.data),
  submitFeedback:(id:string,payload:{clarity_rating:number;usefulness_rating:number;ease_of_use_rating:number;recommendation_trust_rating:number;comments:string|null})=>apiClient.post(`/projects/${id}/feedback`,payload).then(r=>r.data),
};
