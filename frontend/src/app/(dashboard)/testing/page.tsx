"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { CheckCircle2, CircleSlash, FlaskConical, Loader2, XCircle, type LucideIcon } from "lucide-react";
import { PageHeader } from "@/components/shared/page-header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { testingService } from "@/services/testing-service";

const suites=["UNIT","INTEGRATION","SYSTEM","UAT","ORT"];
export default function Testing(){
  const summary=useQuery({queryKey:["testing-summary"],queryFn:testingService.summary});
  const uat=useQuery({queryKey:["uat-summary"],queryFn:testingService.uatSummary});
  if(summary.isLoading||uat.isLoading)return <div className="grid min-h-64 place-items-center"><Loader2 className="size-6 animate-spin"/></div>;
  return <div className="grid gap-6"><PageHeader eyebrow="Testing" title="Testing Dashboard" description="Test and user-acceptance evidence loaded from the database." actions={<Button asChild variant="outline"><Link href="/testing/model-evaluation">Model Evaluation</Link></Button>}/><div className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">{suites.map(key=>{const row=summary.data?.byType?.[key]??{total:0,passed:0,failed:0};return <Card key={key}><CardHeader><div className="flex items-center justify-between"><FlaskConical className="size-5 text-emerald-500"/><Badge>{row.total?`${row.total} RUNS`:"NO DATA"}</Badge></div><CardTitle className="mt-4">{key}</CardTitle></CardHeader><CardContent><div className="grid grid-cols-3 gap-2 text-center"><Score icon={CheckCircle2} label="Passed" value={row.passed}/><Score icon={XCircle} label="Failed" value={row.failed}/><Score icon={CircleSlash} label="Total" value={row.total}/></div></CardContent></Card>})}</div><Card><CardHeader><CardTitle>User Acceptance Summary</CardTitle></CardHeader><CardContent className="grid gap-3 md:grid-cols-4">{[["Responses",uat.data?.count],["Clarity",uat.data?.clarity],["Usefulness",uat.data?.usefulness],["Trust",uat.data?.trust]].map(([label,value])=><div key={label} className="rounded-xl border p-4 text-sm font-semibold">{label}<div className="mt-2 text-2xl font-black">{value??"—"}</div></div>)}</CardContent></Card></div>;
}
function Score({icon:Icon,label,value}:{icon:LucideIcon;label:string;value:number}){return <div className="rounded-xl bg-[var(--muted)] p-2"><Icon className="mx-auto size-4 text-[var(--muted-foreground)]"/><div className="mt-1 text-xs font-bold">{label}</div><div className="font-black">{value}</div></div>}
