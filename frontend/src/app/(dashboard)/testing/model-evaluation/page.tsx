"use client";

import { useQuery } from "@tanstack/react-query";
import { BarChart3, BrainCircuit, Loader2, Target, type LucideIcon } from "lucide-react";
import { PageHeader } from "@/components/shared/page-header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { testingService } from "@/services/testing-service";

const charts:Array<[string,LucideIcon,string]>=[["Confusion Matrix",Target,"confusionMatrix"],["Class Distribution",BarChart3,"classDistribution"],["Model Details",BrainCircuit,"algorithm"]];
export default function ModelEval(){const query=useQuery({queryKey:["model-evaluation"],queryFn:testingService.modelEvaluation});if(query.isLoading)return <div className="grid min-h-64 place-items-center"><Loader2 className="size-6 animate-spin"/></div>;const model=query.data?.activeModel;return <div className="grid gap-6"><PageHeader eyebrow="Testing" title="Model Evaluation" description="Accuracy and evaluation evidence loaded from the active database model version."/><div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">{[["Accuracy",model?.accuracy],["Precision",model?.precision],["Recall",model?.recall],["F1",model?.f1]].map(([label,value])=><Card key={label}><CardContent className="p-5 pt-5"><Badge>{model?model.version:"NO ACTIVE MODEL"}</Badge><div className="mt-5 text-sm text-[var(--muted-foreground)]">{label}</div><div className="mt-1 text-3xl font-black">{typeof value==="number"?`${(value*100).toFixed(1)}%`:"—"}</div></CardContent></Card>)}</div><div className="grid gap-4 lg:grid-cols-3">{charts.map(([title,Icon,key])=><Card key={title}><CardHeader><CardTitle>{title}</CardTitle></CardHeader><CardContent><div className="min-h-64 rounded-2xl border bg-[var(--muted)] p-5"><Icon className="size-8 text-emerald-500"/><pre className="mt-4 whitespace-pre-wrap break-words text-xs">{model?JSON.stringify(model[key],null,2):"No model evaluation data yet."}</pre></div></CardContent></Card>)}</div></div>}
