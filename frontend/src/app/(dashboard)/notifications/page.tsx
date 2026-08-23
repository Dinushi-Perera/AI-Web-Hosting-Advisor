"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Bell, CheckCheck, Loader2, Trash2 } from "lucide-react";
import { toast } from "sonner";
import { PageHeader } from "@/components/shared/page-header";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { notificationService } from "@/services/notification-service";

export default function NotificationsPage(){
  const client=useQueryClient(); const query=useQuery({queryKey:["notifications"],queryFn:notificationService.list});
  const refresh=()=>client.invalidateQueries({queryKey:["notifications"]});
  const read=useMutation({mutationFn:notificationService.read,onSuccess:refresh,onError:()=>toast.error("Could not update notification")});
  const readAll=useMutation({mutationFn:notificationService.readAll,onSuccess:()=>{refresh();toast.success("All notifications marked as read")},onError:()=>toast.error("Could not update notifications")});
  const remove=useMutation({mutationFn:notificationService.remove,onSuccess:()=>{refresh();toast.success("Notification deleted")},onError:()=>toast.error("Could not delete notification")});
  return <div className="grid gap-6"><PageHeader eyebrow="Account" title="Notifications" description="Notification status is synchronized with the database." actions={<Button variant="outline" disabled={readAll.isPending||!query.data?.some(n=>!n.isRead)} onClick={()=>readAll.mutate()}><CheckCheck className="size-4"/>Mark all read</Button>}/>{query.isLoading?<div className="grid min-h-48 place-items-center"><Loader2 className="size-6 animate-spin"/></div>:query.data?.length?<div className="grid gap-3">{query.data.map(n=><Card key={n.id} className={!n.isRead?"border-emerald-500/30":""}><CardContent className="flex gap-4 p-5 pt-5"><span className="grid size-10 shrink-0 place-items-center rounded-xl bg-emerald-500/10 text-emerald-500"><Bell className="size-4"/></span><div className="min-w-0 flex-1"><div className="font-black">{n.title}</div><p className="mt-1 text-sm text-[var(--muted-foreground)]">{n.message}</p><div className="mt-2 text-xs text-[var(--muted-foreground)]">{new Date(n.createdAt).toLocaleString()}</div></div><div className="flex gap-1">{!n.isRead&&<Button size="sm" variant="outline" onClick={()=>read.mutate(n.id)}>Mark read</Button>}<Button size="icon" variant="ghost" title="Delete notification" onClick={()=>remove.mutate(n.id)}><Trash2 className="size-4"/></Button></div></CardContent></Card>)}</div>:<div className="rounded-2xl border p-10 text-center text-sm text-[var(--muted-foreground)]">No notifications yet.</div>}</div>;
}
