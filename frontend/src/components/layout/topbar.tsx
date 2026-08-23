"use client";

import Link from "next/link";
import { Bell, UserCircle2 } from "lucide-react";
import { usePathname } from "next/navigation";
import { Button } from "@/components/ui/button";
import { ThemeToggle } from "./theme-toggle";

export function Topbar() {
  const path = usePathname();
  const crumb = path.split("/").filter(Boolean).map((segment) => segment.replaceAll("-", " "));

  return <header className="sticky top-0 z-30 flex h-16 items-center justify-between gap-3 border-b bg-[var(--background)]/85 px-4 backdrop-blur-xl md:px-6">
    <div className="min-w-0">
      <div className="truncate text-xs text-[var(--muted-foreground)]">{crumb.slice(0, -1).join(" / ") || "Workspace"}</div>
      <div className="truncate text-sm font-bold capitalize">{crumb.at(-1) || "Dashboard"}</div>
    </div>
    <div className="flex items-center gap-1.5">
      <Button asChild variant="ghost" size="icon" title="Notifications">
        <Link href="/notifications"><Bell className="size-4"/><span className="sr-only">Notifications</span></Link>
      </Button>
      <ThemeToggle/>
      <Button asChild variant="ghost" size="icon" title="Profile">
        <Link href="/settings/profile"><UserCircle2 className="size-5"/><span className="sr-only">Profile</span></Link>
      </Button>
    </div>
  </header>;
}
