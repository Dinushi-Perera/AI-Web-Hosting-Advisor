import type { Metadata } from "next";
import "./globals.css";
import { Providers } from "@/components/providers";

export const metadata: Metadata = {
  title: { default: "AI Web Hosting Advisor", template: "%s | AI Web Hosting Advisor" },
  description: "AI-assisted performance auditing, workload estimation, infrastructure comparison and cost-aware hosting recommendations.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en" suppressHydrationWarning><body><a href="#main-content" className="sr-only focus:not-sr-only focus:fixed focus:left-3 focus:top-3 focus:z-[100] focus:rounded-lg focus:bg-[var(--card)] focus:p-3">Skip to content</a><Providers>{children}</Providers></body></html>;
}
