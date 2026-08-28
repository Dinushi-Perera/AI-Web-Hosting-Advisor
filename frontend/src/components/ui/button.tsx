import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const buttonVariants = cva("inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-xl text-sm font-semibold transition-all duration-200 disabled:pointer-events-none disabled:opacity-50 active:scale-[.98] motion-safe:hover:-translate-y-0.5", {
  variants: {
    variant: {
      default: "bg-[var(--primary)] text-[var(--primary-foreground)] shadow-sm hover:brightness-105 hover:shadow-md",
      secondary: "bg-[var(--muted)] text-[var(--foreground)] hover:brightness-95",
      outline: "border bg-[var(--card)] hover:bg-[var(--muted)]",
      ghost: "hover:bg-[var(--muted)]",
      danger: "bg-[var(--danger)] text-white hover:brightness-105",
      gradient: "bg-gradient-to-r from-indigo-600 via-violet-600 to-cyan-500 text-white shadow-lg shadow-indigo-500/25 hover:brightness-110 hover:shadow-xl hover:shadow-violet-500/20",
    },
    size: { sm: "h-9 px-3", md: "h-10 px-4", lg: "h-12 px-5 text-base", icon: "size-10" },
  },
  defaultVariants: { variant: "default", size: "md" },
});

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement>, VariantProps<typeof buttonVariants> { asChild?: boolean }
export function Button({ className, variant, size, asChild, ...props }: ButtonProps) {
  const Comp = asChild ? Slot : "button";
  return <Comp className={cn(buttonVariants({ variant, size }), className)} {...props} />;
}
