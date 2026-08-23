"use client";

import { useEffect, useMemo } from "react";
import { useParams, useRouter } from "next/navigation";
import { useMutation, useQuery } from "@tanstack/react-query";
import { BrainCircuit, CheckCircle2, CloudCog, Loader2, Pause, XCircle } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { analysisService } from "@/services/analysis-service";
import { projectService } from "@/services/project-service";

type JobStage = { key?: string; name?: string; label?: string; status: string };
type JobStatus = { job_id: string; status: string; progress: number; completed_stages: number; total_stages: number; stages: JobStage[]; error_message?: string };

export default function Processing() {
  const router = useRouter();
  const { id } = useParams<{ id: string }>();
  const history = useQuery({ queryKey: ["project-history", id], queryFn: () => projectService.history(id), refetchInterval: q => q.state.data?.runs?.[0]?.jobId ? false : 1000 });
  const jobId = history.data?.runs?.[0]?.jobId as string | undefined;
  const job = useQuery<JobStatus>({ queryKey: ["analysis-job", jobId], queryFn: () => analysisService.status(jobId!), enabled: !!jobId, refetchInterval: q => ["COMPLETED", "FAILED", "CANCELLED"].includes(q.state.data?.status ?? "") ? false : 1500 });
  const cancel = useMutation({ mutationFn: () => analysisService.cancel(jobId!), onSuccess: () => { toast.success("Analysis cancelled in the database"); job.refetch(); }, onError: () => toast.error("Could not cancel the analysis") });
  useEffect(() => { if (job.data?.status === "COMPLETED") { const timer = setTimeout(() => router.replace(`/projects/${id}`), 700); return () => clearTimeout(timer); } }, [id, job.data?.status, router]);
  const stages = useMemo(() => job.data?.stages ?? [], [job.data?.stages]);
  const progress = Math.max(0, Math.min(100, Math.round(job.data?.progress ?? 0)));
  const terminal = ["COMPLETED", "FAILED", "CANCELLED"].includes(job.data?.status ?? "");
  if (history.isError || job.isError) return <div className="grid min-h-64 place-items-center text-center"><div><p className="font-bold text-[var(--danger)]">The analysis status could not be loaded.</p><Button className="mt-4" variant="outline" onClick={() => { history.refetch(); job.refetch(); }}>Try again</Button></div></div>;
  return <div className="mx-auto max-w-3xl py-8">
    <div className="text-center"><div className="relative mx-auto grid size-28 place-items-center rounded-[36px] bg-gradient-to-br from-emerald-600 to-amber-600 text-white shadow-2xl shadow-emerald-500/25"><CloudCog className="size-11"/><span className="absolute -right-2 -top-2 grid size-10 place-items-center rounded-2xl border bg-[var(--card)] text-emerald-500"><BrainCircuit className="size-5"/></span></div><h1 className="mt-7 text-3xl font-black">Analysing infrastructure requirements...</h1><p className="mt-2 text-[var(--muted-foreground)]">Progress is read from the backend analysis job and remains available if you leave this page.</p><div className="mx-auto mt-6 max-w-lg"><div className="mb-2 flex justify-between text-sm font-bold"><span>{job.data?.completed_stages ?? 0} of {job.data?.total_stages ?? stages.length} stages complete</span><span>{progress}%</span></div><Progress value={progress}/></div></div>
    <Card className="mt-8"><CardContent className="grid gap-2 p-4 pt-4">{!jobId || job.isLoading ? <div className="flex items-center justify-center gap-2 p-8"><Loader2 className="size-5 animate-spin"/>Starting analysis job...</div> : stages.map((stage, index) => { const complete=stage.status==="COMPLETED", running=stage.status==="RUNNING"; const label=stage.label||stage.name||stage.key||`Stage ${index+1}`; return <div key={stage.key||label} className="flex items-center gap-3 rounded-xl p-3 hover:bg-[var(--muted)]"><span className={`grid size-9 place-items-center rounded-xl ${complete?"bg-green-500/10 text-green-600":running?"bg-emerald-500/10 text-emerald-500":"bg-[var(--muted)] text-[var(--muted-foreground)]"}`}>{complete?<CheckCircle2 className="size-4"/>:running?<Loader2 className="size-4 animate-spin"/>:<span className="size-2 rounded-full bg-current"/>}</span><span className="flex-1 text-sm font-semibold">{label}</span><span className="text-xs text-[var(--muted-foreground)]">{complete?"Completed":running?"Running":"Pending"}</span></div>; })}</CardContent></Card>
    {job.data?.error_message && <p className="mt-4 rounded-xl border border-red-500/20 bg-red-500/5 p-4 text-sm text-[var(--danger)]">{job.data.error_message}</p>}
    <div className="mt-4 flex justify-center gap-2"><Button variant="outline" onClick={() => router.push("/projects")}><Pause className="size-4"/>Run in Background</Button><Button variant="danger" disabled={!jobId||terminal||cancel.isPending} onClick={() => cancel.mutate()}>{cancel.isPending?<Loader2 className="size-4 animate-spin"/>:<XCircle className="size-4"/>}Cancel Analysis</Button></div>
  </div>;
}
