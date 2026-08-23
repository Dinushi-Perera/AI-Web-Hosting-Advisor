import { apiClient } from "./api-client";

export const reportService = {
  list: () => apiClient.get("/reports").then(r => r.data),
  listForProject: (projectId: string) => apiClient.get(`/projects/${projectId}/reports`).then(r => r.data),
  get: (reportId: string) => apiClient.get(`/reports/${reportId}`).then(r => r.data),
  generate: (projectId: string) => apiClient.post(`/projects/${projectId}/reports`).then(r => r.data),
  download: (reportId: string) => apiClient.get(`/reports/${reportId}/pdf`, { responseType: "blob" }).then(r => r.data),
  remove: (reportId: string) => apiClient.delete(`/reports/${reportId}`).then(r => r.data),
  regenerate: (reportId: string) => apiClient.post(`/reports/${reportId}/regenerate`).then(r => r.data),
};

export function savePdf(blob: Blob, filename: string) {
  const url=URL.createObjectURL(blob); const anchor=document.createElement("a");
  anchor.href=url; anchor.download=filename; document.body.appendChild(anchor); anchor.click(); anchor.remove();
  setTimeout(()=>URL.revokeObjectURL(url),1000);
}

export function printPdf(blob: Blob) {
  const url=URL.createObjectURL(blob); const frame=document.createElement("iframe");
  frame.style.position="fixed"; frame.style.width="1px"; frame.style.height="1px"; frame.style.opacity="0";
  frame.src=url; frame.onload=()=>{frame.contentWindow?.focus();frame.contentWindow?.print();setTimeout(()=>{frame.remove();URL.revokeObjectURL(url)},60_000)};
  document.body.appendChild(frame);
}
