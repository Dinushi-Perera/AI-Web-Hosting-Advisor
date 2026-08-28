"use client";
import CountUp from "react-countup";
import type { ComponentType, SVGProps } from "react";
import { Card } from "@/components/ui/card";
type MetricIcon=ComponentType<SVGProps<SVGSVGElement>&{size?:number|string;color?:string;weight?:"Filled"|"Outline"}>;
const tones=["from-indigo-500/20 to-cyan-500/10 text-indigo-600 dark:text-indigo-300","from-cyan-500/20 to-blue-500/10 text-cyan-600 dark:text-cyan-300","from-violet-500/20 to-fuchsia-500/10 text-violet-600 dark:text-violet-300","from-amber-500/20 to-orange-500/10 text-amber-600 dark:text-amber-300"];
export function StatCard({label,value,suffix="",trend,icon:Icon,tone=0}:{label:string;value:number;suffix?:string;trend?:string;icon:MetricIcon;tone?:number}){return <Card className="card-hover overflow-hidden p-5"><div className="flex items-start justify-between"><div><div className="text-sm font-medium text-[var(--muted-foreground)]">{label}</div><div className="mt-2 text-3xl font-black tracking-tight"><CountUp end={value} duration={1.1}/>{suffix}</div></div><span className={`grid size-11 place-items-center rounded-2xl bg-gradient-to-br ${tones[tone%tones.length]}`}><Icon className="size-5" color="currentColor"/></span></div>{trend&&<div className="mt-4 border-t pt-3 text-xs font-semibold text-[var(--muted-foreground)]">{trend}</div>}</Card>}
