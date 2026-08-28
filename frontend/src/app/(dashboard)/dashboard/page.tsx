"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { Loader2 } from "lucide-react";
import { Activity, Add, Chart, Cloud, Cpu, DocumentText, DollarCircle, Magicpen, ShieldTick, StatusUp } from "reicon-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { StatCard } from "@/components/dashboard/stat-card";
import { CostChart, HostingDistribution, PerformanceChart } from "@/components/charts/dashboard-charts";
import { greeting } from "@/lib/utils";
import { StatusBadge } from "@/components/shared/status-badge";
import { dashboardService } from "@/services/dashboard-service";
import { userService } from "@/services/user-service";

export default function DashboardPage(){
  const dashboard=useQuery({queryKey:["dashboard"],queryFn:dashboardService.get,staleTime:10_000,refetchInterval:30_000,refetchOnWindowFocus:true});
  const profile=useQuery({queryKey:["profile"],queryFn:userService.me});
  if(dashboard.isLoading)return <div className="grid min-h-72 place-items-center"><Loader2 className="size-7 animate-spin text-indigo-500"/></div>;
  if(dashboard.isError)return <div className="rounded-2xl border p-10 text-center"><p>Could not load your dashboard.</p><Button className="mt-4" variant="outline" onClick={()=>dashboard.refetch()}>Try again</Button></div>;

  const data=dashboard.data!;const summary=data.summary;const first=data.recent_projects[0];
  return <div className="grid gap-6">
    <Card className="aurora-border tech-grid overflow-hidden border-0">
      <CardContent className="relative grid gap-8 p-6 pt-6 lg:grid-cols-[1fr_auto] lg:items-center lg:p-8">
        <div className="absolute -right-20 -top-28 size-72 rounded-full bg-cyan-400/15 blur-3xl"/><div className="absolute -bottom-36 left-1/3 size-72 rounded-full bg-violet-500/15 blur-3xl"/>
        <div className="relative">
          <div className="mb-4 inline-flex items-center gap-2 rounded-full border bg-[var(--card)]/70 px-3 py-1.5 text-xs font-bold text-[var(--muted-foreground)] shadow-sm"><span className="live-dot size-2 rounded-full bg-[var(--success)]"/>Live decision workspace</div>
          <h1 className="max-w-3xl text-3xl font-black tracking-[-.04em] md:text-5xl">{greeting()}, <span className="gradient-text">{profile.data?.fullName?.split(" ")[0]||"there"}</span></h1>
          <p className="mt-3 max-w-2xl text-sm leading-6 text-[var(--muted-foreground)] md:text-base">Realtime, database-backed infrastructure intelligence across performance, workload, architecture, cost, testing, and optimization.</p>
        </div>
        <Button asChild variant="gradient" size="lg" className="relative shadow-2xl"><Link href="/projects/new"><Add className="size-5" color="currentColor" weight="Filled"/>Start new analysis</Link></Button>
      </CardContent>
    </Card>

    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-6">
      <StatCard label="Total Projects" value={summary.total_projects} icon={Cloud} tone={0}/>
      <StatCard label="Completed Analyses" value={summary.completed_analyses} icon={StatusUp} tone={1}/>
      <StatCard label="Average Performance" value={summary.average_performance_score??0} suffix="/100" trend={summary.average_performance_score===null?"No measured audits":"Measured evidence"} icon={Cpu} tone={2}/>
      <StatCard label="Monthly Savings" value={summary.estimated_monthly_savings??0} suffix="$" trend={summary.estimated_monthly_savings===null?"Needs current-cost evidence":"Estimated"} icon={DollarCircle} tone={3}/>
      <StatCard label="Reports Generated" value={summary.reports_generated} icon={DocumentText} tone={0}/>
      <StatCard label="Priority Issues" value={summary.high_priority_issues} icon={ShieldTick} tone={3}/>
    </div>

    <div className="grid gap-4 xl:grid-cols-3">
      <Card className="card-hover xl:col-span-2"><ChartHeading icon={Chart} title="Performance intelligence" description="Measured scores from the stored analysis history."/><CardContent><PerformanceChart data={data.performance_trend}/></CardContent></Card>
      <Card className="card-hover"><ChartHeading icon={Cloud} title="Architecture mix" description="Distribution of completed hosting decisions."/><CardContent><HostingDistribution data={data.hosting_distribution}/></CardContent></Card>
    </div>

    <div className="grid gap-4 xl:grid-cols-3">
      <Card className="card-hover xl:col-span-2"><ChartHeading icon={DollarCircle} title="Monthly cost intelligence" description="Every persisted analysis adds a USD cost point; current cost appears only when supplied."/><CardContent><CostChart data={data.cost_trend}/></CardContent></Card>
      <Card className="aurora-border overflow-hidden border-0 bg-gradient-to-br from-indigo-500/10 via-violet-500/10 to-cyan-500/10"><CardHeader><span className="mb-3 grid size-12 place-items-center rounded-2xl bg-gradient-to-br from-indigo-600 via-violet-600 to-cyan-500 text-white shadow-lg shadow-indigo-500/25"><Magicpen className="size-6" color="currentColor" weight="Filled"/></span><CardTitle>Next best action</CardTitle><CardDescription>Your most recently updated project.</CardDescription></CardHeader><CardContent>{first?<><p className="text-sm leading-6">{first.recommendation?`${first.recommendation} is currently recommended for ${first.name}.`:`${first.name} is waiting for a completed recommendation.`}</p><Button variant="outline" className="mt-4" asChild><Link href={`/projects/${first.id}/recommendation`}>Open recommendation</Link></Button></>:<p className="text-sm text-[var(--muted-foreground)]">Create a project to receive an evidence-backed recommendation.</p>}</CardContent></Card>
    </div>

    <div className="grid gap-4 xl:grid-cols-[1.35fr_.65fr]">
      <Card><CardHeader className="flex-row items-center justify-between"><div><CardTitle>Recent projects</CardTitle><CardDescription>Latest persisted analyses and outcomes.</CardDescription></div><Button variant="ghost" asChild><Link href="/projects">View all</Link></Button></CardHeader><CardContent className="grid gap-3">{data.recent_projects.length?data.recent_projects.map((project,index)=><Link key={project.id} href={`/projects/${project.id}`} className="group grid gap-3 rounded-2xl border bg-gradient-to-r from-indigo-500/[.04] to-cyan-500/[.04] p-4 transition-all hover:-translate-y-0.5 hover:border-indigo-500/30 hover:shadow-lg md:grid-cols-[auto_1fr_auto_auto] md:items-center"><span className={`grid size-10 place-items-center rounded-xl ${index%2?"bg-cyan-500/10 text-cyan-600":"bg-indigo-500/10 text-indigo-600"}`}><Cloud className="size-5" color="currentColor"/></span><div><div className="font-bold">{project.name}</div><div className="text-xs text-[var(--muted-foreground)]">{project.mode} · {project.website||"No live URL"}</div></div><StatusBadge status={project.status}/><div className="text-sm font-semibold">{project.recommendation||"Pending"}</div></Link>):<Empty text="No projects yet."/>}</CardContent></Card>
      <div className="grid gap-4"><Card><ChartHeading icon={Activity} title="Realtime activity" description="Latest database audit events."/><CardContent className="grid gap-1">{data.recent_activity?.length?data.recent_activity.slice(0,6).map((item,index)=><div key={item.id} className="relative flex gap-3 py-2"><div className="relative mt-1"><span className="block size-2.5 rounded-full bg-gradient-to-br from-indigo-500 to-cyan-400"/>{index<data.recent_activity.length-1&&<span className="absolute left-1 top-3 h-8 w-px bg-[var(--border)]"/>}</div><div className="min-w-0"><div className="truncate text-xs font-bold">{item.action.replaceAll("_"," ")}</div><div className="truncate text-[11px] text-[var(--muted-foreground)]">{item.projectTitle||"Workspace"} · {new Date(item.timestamp).toLocaleString()}</div></div></div>):<Empty text="No activity recorded yet."/>}</CardContent></Card><Card><ChartHeading icon={ShieldTick} title="Priority issues" description="Open high-priority optimization work."/><CardContent>{summary.high_priority_issues&&first?<Link href={`/projects/${first.id}/optimization`} className="block rounded-xl border border-amber-500/20 bg-amber-500/10 p-4 transition-transform hover:-translate-y-0.5"><div className="mb-1 text-xs font-black uppercase tracking-wide text-amber-600 dark:text-amber-300">Needs attention</div><div className="text-sm font-semibold">{summary.high_priority_issues} high-priority item{summary.high_priority_issues===1?"":"s"}</div></Link>:<Empty text="No high-priority issues."/>}</CardContent></Card></div>
    </div>
  </div>;
}

type ReiconComponent=React.ComponentType<React.SVGProps<SVGSVGElement>&{size?:number|string;color?:string;weight?:"Filled"|"Outline"}>;
function ChartHeading({icon:Icon,title,description}:{icon:ReiconComponent;title:string;description:string}){return <CardHeader><div className="flex items-start gap-3"><span className="grid size-10 shrink-0 place-items-center rounded-xl bg-gradient-to-br from-indigo-500/15 to-cyan-500/15 text-indigo-600 dark:text-indigo-300"><Icon className="size-5" color="currentColor"/></span><div><CardTitle>{title}</CardTitle><CardDescription>{description}</CardDescription></div></div></CardHeader>}
function Empty({text}:{text:string}){return <div className="rounded-xl border border-dashed p-6 text-center text-sm text-[var(--muted-foreground)]">{text}</div>}
