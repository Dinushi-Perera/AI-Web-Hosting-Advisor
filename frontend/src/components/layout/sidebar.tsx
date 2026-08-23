"use client";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useState } from "react";
import { ChevronLeft, ChevronRight, CloudCog, Loader2, LogOut } from "lucide-react";
import { toast } from "sonner";
import { navGroups } from "@/constants/navigation";
import { useUIStore } from "@/store/ui-store";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { authService } from "@/services/auth-service";

export function Sidebar() {
  const path=usePathname(); const router=useRouter(); const {sidebarCollapsed,toggleSidebar}=useUIStore();
  const [loggingOut,setLoggingOut]=useState(false);
  const logout=async()=>{if(loggingOut)return;setLoggingOut(true);try{await authService.logout();toast.success("Signed out safely");router.replace("/");router.refresh()}catch(error){toast.error(error&&typeof error==="object"&&"message" in error?String(error.message):"Could not sign out. Please try again.");setLoggingOut(false)}};
  return <aside className={cn("sticky top-0 hidden h-screen shrink-0 border-r bg-[var(--card)] lg:flex lg:flex-col transition-[width] duration-200", sidebarCollapsed?"w-[82px]":"w-[270px]") }>
    <div className="flex h-16 items-center gap-3 border-b px-4"><div className="pulse-ring grid size-10 shrink-0 place-items-center rounded-2xl bg-gradient-to-br from-emerald-700 to-amber-500 text-white shadow-lg shadow-emerald-500/20"><CloudCog className="size-5"/></div>{!sidebarCollapsed&&<div className="min-w-0"><div className="truncate font-black">AI Hosting Advisor</div><div className="text-[11px] text-[var(--muted-foreground)]">Decision Support Platform</div></div>}</div>
    <nav className="flex-1 overflow-y-auto px-3 py-4">{navGroups.map(group=><div key={group.label} className="mb-5">{!sidebarCollapsed&&<div className="mb-2 px-2 text-[10px] font-black uppercase tracking-[.18em] text-[var(--muted-foreground)]">{group.label}</div>}<div className="grid gap-1">{group.items.map(item=>{const active=path===item.href || (item.href!=="/dashboard"&&path.startsWith(item.href.split('#')[0])); const Icon=item.icon; return <Link key={item.label} href={item.href} title={sidebarCollapsed?item.label:undefined} className={cn("flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-semibold transition-colors",active?"bg-emerald-500/10 text-emerald-600 dark:text-emerald-300":"text-[var(--muted-foreground)] hover:bg-[var(--muted)] hover:text-[var(--foreground)]",sidebarCollapsed&&"justify-center px-0")}><Icon className="size-4 shrink-0"/>{!sidebarCollapsed&&<span>{item.label}</span>}</Link>})}</div></div>)}
    </nav>
    <div className="grid gap-1 border-t p-3">
      <Button variant="ghost" className={cn("w-full",sidebarCollapsed?"px-0":"justify-between")} onClick={toggleSidebar} title={sidebarCollapsed?"Expand sidebar":undefined}>{!sidebarCollapsed&&"Collapse"}{sidebarCollapsed?<ChevronRight className="size-4"/>:<ChevronLeft className="size-4"/>}</Button>
      <Button variant="ghost" className={cn("w-full text-[var(--danger)] hover:bg-red-500/10 hover:text-[var(--danger)]",sidebarCollapsed?"px-0":"justify-start")} onClick={logout} disabled={loggingOut} title={sidebarCollapsed?"Log out":undefined} aria-label="Log out and return to public website">{loggingOut?<Loader2 className="size-4 animate-spin"/>:<LogOut className="size-4"/>}{!sidebarCollapsed&&<span>{loggingOut?"Logging out...":"Log out"}</span>}</Button>
    </div>
  </aside>;
}
