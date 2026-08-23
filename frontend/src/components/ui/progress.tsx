import { cn } from "@/lib/utils";
export function Progress({ value, className }: { value: number; className?: string }) { return <div className={cn("h-2 overflow-hidden rounded-full bg-[var(--muted)]", className)}><div className="h-full rounded-full bg-gradient-to-r from-emerald-500 to-amber-500 transition-all duration-300" style={{ width: `${Math.max(0, Math.min(100, value))}%` }} /></div>; }
