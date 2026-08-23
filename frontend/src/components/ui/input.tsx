import * as React from "react";
import { cn } from "@/lib/utils";
export const Input = React.forwardRef<HTMLInputElement, React.ComponentProps<"input">>(({ className, ...props }, ref) => <input ref={ref} className={cn("h-11 w-full rounded-xl border bg-[var(--card)] px-3 text-sm shadow-sm placeholder:text-[var(--muted-foreground)]", className)} {...props} />);
Input.displayName = "Input";
export const Textarea = React.forwardRef<HTMLTextAreaElement, React.ComponentProps<"textarea">>(({ className, ...props }, ref) => <textarea ref={ref} className={cn("min-h-28 w-full rounded-xl border bg-[var(--card)] px-3 py-3 text-sm shadow-sm placeholder:text-[var(--muted-foreground)]", className)} {...props} />);
Textarea.displayName = "Textarea";
export const Select = React.forwardRef<HTMLSelectElement, React.ComponentProps<"select">>(({ className, ...props }, ref) => <select ref={ref} className={cn("h-11 w-full rounded-xl border bg-[var(--card)] px-3 text-sm shadow-sm", className)} {...props} />);
Select.displayName = "Select";
