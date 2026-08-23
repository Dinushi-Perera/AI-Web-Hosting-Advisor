"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { Copy, FileText, Loader2, RefreshCw } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { StatusBadge } from "@/components/shared/status-badge";
import { projectService } from "@/services/project-service";
import { reportService } from "@/services/report-service";

export function ProjectHeader({id}:{id:string}){
  const router=useRouter(); const project=useQuery({queryKey:["project",id],queryFn:()=>projectService.get(id)});
  const rerun=useMutation({mutationFn:()=>projectService.analyse(id),onSuccess:()=>{toast.success("Analysis queued");router.push(`/projects/${id}/processing`)},onError:()=>toast.error("Could not queue analysis")});
  const report=useMutation({mutationFn:()=>reportService.generate(id),onSuccess:()=>{toast.success("Report generated and saved");router.push(`/projects/${id}/report`)},onError:(e)=>toast.error(e&&typeof e==="object"&&"message" in e?String(e.message):"Could not generate report")});
  const copy=async()=>{if(!project.data)return;await navigator.clipboard.writeText(`${project.data.name}\nMode: ${project.data.mode}\nStatus: ${project.data.status}\nRecommendation: ${project.data.recommendation||"Pending"}\nCost: ${project.data.costRange?`USD ${project.data.costRange[0]}-${project.data.costRange[1]}`:"Unavailable"}`);toast.success("Project summary copied")};
  if(project.isLoading)return <div className="h-24 animate-pulse rounded-2xl bg-[var(--muted)]"/>;
  if(project.isError)return <div className="rounded-2xl border p-5">Could not load project header. <Button className="ml-2" size="sm" variant="outline" onClick={()=>project.refetch()}>Retry</Button></div>;
  const p=project.data!;
  return <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between"><div><div className="mb-2 flex flex-wrap items-center gap-2"><Badge>{p.mode}</Badge><StatusBadge status={p.status}/></div><h1 className="text-3xl font-black tracking-tight">{p.name}</h1><p className="mt-2 text-sm text-[var(--muted-foreground)]">Last updated {new Date(p.updatedAt).toLocaleString()} · {p.website??"No live URL"}</p></div><div className="flex flex-wrap gap-2"><Button variant="outline" disabled={rerun.isPending} onClick={()=>rerun.mutate()}>{rerun.isPending?<Loader2 className="size-4 animate-spin"/>:<RefreshCw className="size-4"/>}Run Again</Button><Button variant="outline" onClick={copy}><Copy className="size-4"/>Copy Summary</Button><Button variant="gradient" disabled={report.isPending||p.status!=="Completed"} onClick={()=>report.mutate()}>{report.isPending?<Loader2 className="size-4 animate-spin"/>:<FileText className="size-4"/>}Generate Report</Button></div></div>;
}
