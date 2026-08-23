"use client";
import { MonitorCog, Moon, Sun } from "lucide-react";
import { useTheme } from "next-themes";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";

export function ThemeToggle() {
  const { theme, setTheme } = useTheme(); const [mounted,setMounted]=useState(false); useEffect(()=>setMounted(true),[]);
  if(!mounted) return <div className="size-10 rounded-xl bg-[var(--muted)]"/>;
  const order = theme === "light" ? "dark" : theme === "dark" ? "system" : "light";
  const Icon = theme === "light" ? Sun : theme === "dark" ? Moon : MonitorCog;
  return <Button variant="ghost" size="icon" onClick={()=>setTheme(order)} aria-label={`Theme: ${theme}. Switch to ${order}`} title={`Theme: ${theme}`}><Icon className="size-4"/></Button>;
}
