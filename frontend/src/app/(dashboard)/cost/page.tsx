"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { Loader2 } from "lucide-react";
import { ProjectSection } from "@/components/projects/project-section";
import { PageHeader } from "@/components/shared/page-header";
import { Button } from "@/components/ui/button";
import { projectService } from "@/services/project-service";

export default function Cost() {
  const projects=useQuery({queryKey:["projects"],queryFn:projectService.list});
  const project=projects.data?.find(item=>item.status==="Completed") ?? projects.data?.[0];
  return <div className="grid gap-6"><PageHeader eyebrow="AI Advisor" title="Cost Explorer" description="Compare the latest project cost range and budget compatibility using database-backed estimates."/>{projects.isLoading?<div className="grid min-h-48 place-items-center"><Loader2 className="size-6 animate-spin"/></div>:project?<ProjectSection section="cost" id={project.id}/>:<div className="rounded-2xl border p-8 text-center"><p className="font-bold">Create a project to calculate a hosting cost range.</p><Button asChild className="mt-4"><Link href="/projects/new">New Analysis</Link></Button></div>}</div>;
}
