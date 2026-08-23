import { apiClient } from "./api-client";

export type Notification = { id:string; type:string; title:string; message:string; isRead:boolean; data?:Record<string,unknown>; createdAt:string };

export const notificationService={
  list:()=>apiClient.get<Notification[]>("/notifications").then(r=>r.data),
  read:(id:string)=>apiClient.patch<Notification>(`/notifications/${id}/read`).then(r=>r.data),
  readAll:()=>apiClient.post("/notifications/read-all").then(r=>r.data),
  remove:(id:string)=>apiClient.delete(`/notifications/${id}`).then(r=>r.data),
};
