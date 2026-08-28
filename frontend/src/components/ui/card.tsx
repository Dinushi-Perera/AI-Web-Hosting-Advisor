import * as React from "react";
import { cn } from "@/lib/utils";
export function Card({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) { return <div className={cn("glass-panel rounded-2xl border bg-[var(--card)] text-[var(--card-foreground)] shadow-[0_1px_2px_var(--shadow),0_12px_34px_-26px_var(--shadow)]", className)} {...props} />; }
export function CardHeader({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) { return <div className={cn("p-5 pb-3", className)} {...props} />; }
export function CardTitle({ className, ...props }: React.HTMLAttributes<HTMLHeadingElement>) { return <h3 className={cn("font-extrabold tracking-[-.02em]", className)} {...props} />; }
export function CardDescription({ className, ...props }: React.HTMLAttributes<HTMLParagraphElement>) { return <p className={cn("mt-1 text-sm text-[var(--muted-foreground)]", className)} {...props} />; }
export function CardContent({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) { return <div className={cn("p-5 pt-2", className)} {...props} />; }
