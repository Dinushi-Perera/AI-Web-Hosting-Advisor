"use client";

import {useEffect,useMemo,useState} from "react";
import Link from "next/link";
import {useQuery} from "@tanstack/react-query";
import {ArrowRight,Loader2} from "lucide-react";
import {AdvancedPerformance} from "@/components/projects/advanced-performance";
import {PageHeader} from "@/components/shared/page-header";
import {Button} from "@/components/ui/button";
import {Card,CardContent} from "@/components/ui/card";
import {Select} from "@/components/ui/input";
import {projectService} from "@/services/project-service";

export default function PerformanceAnalysisPage(){
 const projects=useQuery({queryKey:["projects"],queryFn:projectService.list});
 const completed=useMemo(()=>(projects.data??[]).filter(project=>project.status==="Completed"),[projects.data]);
 const [projectId,setProjectId]=useState("");
 useEffect(()=>{if(!projectId&&completed[0])setProjectId(completed[0].id)},[completed,projectId]);
 const selected=completed.find(project=>project.id===projectId);
 if(projects.isLoading)return <div className="grid min-h-72 place-items-center"><Loader2 className="size-7 animate-spin text-indigo-500"/></div>;
 return <div className="grid gap-6"><PageHeader eyebrow="AI Advisor" title="Performance Analysis" description="Explore PageSpeed, Lighthouse, Core Web Vitals, device differences, trends, and improvement opportunities for every analysed project."/>{completed.length?<><Card><CardContent className="grid gap-4 p-5 pt-5 md:grid-cols-[1fr_auto] md:items-end"><label className="grid gap-2 text-sm font-bold">Analysed project<Select value={projectId} onChange={event=>setProjectId(event.target.value)}>{completed.map(project=><option key={project.id} value={project.id}>{project.name} · {project.mode}</option>)}</Select></label>{selected&&<Button asChild variant="outline"><Link href={`/projects/${selected.id}/performance`}>Open project details<ArrowRight className="size-4"/></Link></Button>}</CardContent></Card>{projectId&&<AdvancedPerformance id={projectId}/>}</>:<Card><CardContent className="p-8 text-center"><p className="font-bold">Complete an analysis to create a performance dashboard.</p><Button asChild className="mt-4"><Link href="/projects/new">New Analysis</Link></Button></CardContent></Card>}</div>
}
