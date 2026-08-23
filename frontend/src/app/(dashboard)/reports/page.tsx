"use client";

import Link from "next/link";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Download, FileText, Loader2, Printer, RefreshCw, Trash2 } from "lucide-react";
import { toast } from "sonner";
import { PageHeader } from "@/components/shared/page-header";
import { Button } from "@/components/ui/button";
import { StatusBadge } from "@/components/shared/status-badge";
import { printPdf, reportService, savePdf } from "@/services/report-service";

type ReportRow={id:string;projectId:string;projectTitle:string;projectMode?:string;recommendation?:string;version:number;generatedAt:string;status:string};
const errorMessage=(e:unknown)=>e&&typeof e==="object"&&"message" in e?String(e.message):"The request could not be completed.";

export default function Reports(){
  const client=useQueryClient(); const query=useQuery({queryKey:["reports"],queryFn:()=>reportService.list() as Promise<ReportRow[]>});
  const refresh=()=>client.invalidateQueries({queryKey:["reports"]});
  const regenerate=useMutation({mutationFn:reportService.regenerate,onSuccess:()=>{refresh();toast.success("A new report version was saved")},onError:e=>toast.error(errorMessage(e))});
  const remove=useMutation({mutationFn:reportService.remove,onSuccess:()=>{refresh();toast.success("Report deleted")},onError:e=>toast.error(errorMessage(e))});
  const download=async(row:ReportRow)=>{try{savePdf(await reportService.download(row.id),`${safeName(row.projectTitle)}-v${row.version}.pdf`);toast.success("PDF download started")}catch(e){toast.error(errorMessage(e))}};
  const print=async(row:ReportRow)=>{try{printPdf(await reportService.download(row.id))}catch(e){toast.error(errorMessage(e))}};
  return <div className="grid gap-6"><PageHeader eyebrow="Reports" title="Generated Reports" description="Reports are loaded from the database and can be downloaded, printed, regenerated or deleted."/>{query.isLoading?<div className="grid min-h-52 place-items-center"><Loader2 className="size-6 animate-spin"/></div>:query.isError?<div className="rounded-2xl border p-8 text-center"><p>{errorMessage(query.error)}</p><Button className="mt-4" variant="outline" onClick={()=>query.refetch()}>Try again</Button></div>:query.data?.length?<div className="overflow-x-auto rounded-2xl border bg-[var(--card)]"><table className="w-full min-w-[860px] text-sm"><thead className="bg-[var(--muted)] text-left text-xs uppercase tracking-wide text-[var(--muted-foreground)]"><tr>{["Report","Project","Mode","Generated","Recommendation","Status","Actions"].map(x=><th key={x} className="px-4 py-3">{x}</th>)}</tr></thead><tbody>{query.data.map(row=><tr key={row.id} className="border-t"><td className="px-4 py-4 font-black"><Link href={`/projects/${row.projectId}/report`} className="flex items-center gap-2"><FileText className="size-4 text-emerald-500"/>{row.projectTitle} v{row.version}</Link></td><td className="px-4">{row.projectTitle}</td><td className="px-4">{display(row.projectMode)}</td><td className="px-4 text-[var(--muted-foreground)]">{new Date(row.generatedAt).toLocaleString()}</td><td className="px-4 font-semibold">{display(row.recommendation)}</td><td className="px-4"><StatusBadge status={row.status}/></td><td className="px-4"><div className="flex gap-1"><Button title="Download PDF" variant="ghost" size="icon" onClick={()=>download(row)}><Download className="size-4"/></Button><Button title="Print PDF" variant="ghost" size="icon" onClick={()=>print(row)}><Printer className="size-4"/></Button><Button title="Regenerate report" variant="ghost" size="icon" disabled={regenerate.isPending} onClick={()=>regenerate.mutate(row.id)}><RefreshCw className="size-4"/></Button><Button title="Delete report" variant="ghost" size="icon" disabled={remove.isPending} onClick={()=>{if(window.confirm(`Delete ${row.projectTitle} report v${row.version}?`))remove.mutate(row.id)}}><Trash2 className="size-4"/></Button></div></td></tr>)}</tbody></table></div>:<div className="rounded-2xl border border-dashed p-10 text-center text-sm text-[var(--muted-foreground)]">No generated reports yet. Generate one from a completed project.</div>}</div>;
}

function safeName(value:string){return value.toLowerCase().replace(/[^a-z0-9]+/g,"-").replace(/^-|-$/g,"")||"hosting-advisor-report"}
function display(value?:string){return value?value.replaceAll("_"," ").replace(/\b\w/g,c=>c.toUpperCase()):"—"}
