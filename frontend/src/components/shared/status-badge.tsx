import { AlertTriangle, CheckCircle2, Clock3, Loader2, XCircle } from "lucide-react";
import { Badge } from "@/components/ui/badge";

export function StatusBadge({ status }: { status: string }) {
  const s = status.toLowerCase();
  const cls = s.includes("complete") || s.includes("good") || s.includes("high confidence") ? "border-green-500/30 bg-green-500/10 text-green-600 dark:text-green-300" : s.includes("fail") || s.includes("poor") ? "border-red-500/30 bg-red-500/10 text-red-600 dark:text-red-300" : s.includes("analys") || s.includes("running") ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-600 dark:text-emerald-300" : "border-amber-500/30 bg-amber-500/10 text-amber-700 dark:text-amber-300";
  const Icon = s.includes("complete") || s.includes("good") ? CheckCircle2 : s.includes("fail") || s.includes("poor") ? XCircle : s.includes("analys") || s.includes("running") ? Loader2 : s.includes("draft") || s.includes("queued") ? Clock3 : AlertTriangle;
  return <Badge className={cls}><Icon className={`size-3.5 ${s.includes("analys") ? "animate-spin" : ""}`} />{status}</Badge>;
}
