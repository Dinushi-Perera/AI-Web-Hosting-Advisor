"use client";
import Link from "next/link";
import { CloudCog } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ThemeToggle } from "@/components/layout/theme-toggle";
export function PublicNav(){return <header className="sticky top-0 z-40 border-b bg-[var(--background)]/80 backdrop-blur-xl"><div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4"><Link href="/" className="flex items-center gap-2 font-black"><span className="grid size-9 place-items-center rounded-xl bg-gradient-to-br from-emerald-600 to-amber-600 text-white"><CloudCog className="size-5"/></span>AI Hosting Advisor</Link><nav className="hidden items-center gap-6 text-sm font-semibold text-[var(--muted-foreground)] md:flex"><a href="#features">Features</a><a href="#how">How it works</a><a href="#compare">Infrastructure</a></nav><div className="flex items-center gap-2"><ThemeToggle/><Button variant="ghost" asChild className="hidden sm:inline-flex"><Link href="/login">Sign in</Link></Button><Button variant="gradient" asChild><Link href="/register">Start Free Analysis</Link></Button></div></div></header>}
