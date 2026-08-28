"use client";

import Link from "next/link";
import { BellRing, CheckCheck, ChevronRight, User } from "lucide-react";
import { usePathname } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { notificationService, type Notification } from "@/services/notification-service";
import { ThemeToggle } from "./theme-toggle";

export function Topbar() {
  const path=usePathname(); const crumb=path.split("/").filter(Boolean).map(segment=>segment.replaceAll("-"," "));
  const [open,setOpen]=useState(false); const queryClient=useQueryClient(); const knownIds=useRef<Set<string>|null>(null);
  const notifications=useQuery({queryKey:["notifications"],queryFn:notificationService.list,refetchInterval:30_000,refetchOnWindowFocus:true});
  const markRead=useMutation({mutationFn:notificationService.read,onSuccess:()=>queryClient.invalidateQueries({queryKey:["notifications"]})});
  const markAll=useMutation({mutationFn:notificationService.readAll,onSuccess:()=>{queryClient.invalidateQueries({queryKey:["notifications"]});toast.success("All notifications are marked as read.")}});
  const items=notifications.data??[]; const unread=items.filter(item=>!item.isRead); const latest=items.slice(0,4);
  useEffect(()=>{if(!notifications.data)return;const ids=new Set(notifications.data.map(item=>item.id));if(knownIds.current){notifications.data.filter(item=>!knownIds.current?.has(item.id)).slice(0,2).forEach(item=>toast(item.title,{description:item.message,duration:5000}));}knownIds.current=ids;},[notifications.data]);
  const visit=(item:Notification)=>{if(!item.isRead)markRead.mutate(item.id);setOpen(false);};
  return <header className="glass-panel sticky top-0 z-30 flex h-16 items-center justify-between gap-3 border-b px-4 md:px-6">
    <div className="min-w-0"><div className="truncate text-xs text-[var(--muted-foreground)]">{crumb.slice(0,-1).join(" / ")||"Workspace"}</div><div className="truncate text-sm font-bold capitalize">{crumb.at(-1)||"Dashboard"}</div></div>
    <div className="flex items-center gap-1.5"><div className="relative"><Button variant="ghost" size="icon" title={unread.length?`${unread.length} unread notifications`:"Notifications"} aria-expanded={open} aria-haspopup="dialog" onClick={()=>setOpen(value=>!value)}><BellRing className="size-5"/><span className="sr-only">Notifications</span></Button>{unread.length>0&&<span className="notification-unread-dot absolute right-1 top-1 size-2.5 rounded-full ring-2 ring-[var(--card)]" aria-label={`${unread.length} unread notifications`}/>} {open&&<NotificationPopup items={latest} unreadCount={unread.length} loading={notifications.isLoading} markAll={()=>markAll.mutate()} markingAll={markAll.isPending} onVisit={visit}/>}</div><ThemeToggle/><Button asChild variant="ghost" size="icon" title="Profile"><Link href="/settings/profile"><User className="size-5"/><span className="sr-only">Profile</span></Link></Button></div>
  </header>;
}

function NotificationPopup({items,unreadCount,loading,markAll,markingAll,onVisit}:{items:Notification[];unreadCount:number;loading:boolean;markAll:()=>void;markingAll:boolean;onVisit:(item:Notification)=>void}){return <section role="dialog" aria-label="Recent notifications" className="absolute right-0 top-12 z-50 w-[min(23rem,calc(100vw-2rem))] overflow-hidden rounded-2xl border bg-[var(--card)] shadow-2xl shadow-[var(--shadow)]"><div className="flex items-center justify-between border-b px-4 py-3"><div><div className="font-black">Notifications</div><div className="text-xs text-[var(--muted-foreground)]">{unreadCount?`${unreadCount} new update${unreadCount===1?"":"s"}`:"You are all caught up"}</div></div><Button variant="ghost" size="sm" disabled={!unreadCount||markingAll} onClick={markAll}><CheckCheck className="size-4"/>Read all</Button></div><div className="max-h-80 overflow-y-auto p-2">{loading?<div className="p-5 text-center text-sm text-[var(--muted-foreground)]">Loading updates…</div>:items.length?items.map(item=><button key={item.id} onClick={()=>onVisit(item)} className="flex w-full gap-3 rounded-xl p-3 text-left transition hover:bg-[var(--muted)]"><span className={`mt-1.5 size-2 shrink-0 rounded-full ${item.isRead?"bg-[var(--border)]":"notification-unread-dot"}`}/><span className="min-w-0 flex-1"><span className="block text-sm font-black">{item.title}</span><span className="mt-1 block line-clamp-2 text-xs leading-5 text-[var(--muted-foreground)]">{item.message}</span><span className="mt-2 block text-[10px] font-bold uppercase tracking-wide text-[var(--muted-foreground)]">{new Date(item.createdAt).toLocaleString()}</span></span></button>):<div className="p-6 text-center text-sm text-[var(--muted-foreground)]">No notifications yet. New analysis and test updates will appear here.</div>}</div><Link href="/notifications" className="flex items-center justify-center gap-2 border-t px-4 py-3 text-sm font-black text-[var(--primary)] transition hover:bg-[var(--muted)]">Open notification center <ChevronRight className="size-4"/></Link></section>}
