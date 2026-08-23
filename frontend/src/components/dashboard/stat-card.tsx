"use client";
import CountUp from "react-countup";
import type { LucideIcon } from "lucide-react";
import { Card } from "@/components/ui/card";
export function StatCard({label,value,suffix="",trend,icon:Icon}:{label:string;value:number;suffix?:string;trend?:string;icon:LucideIcon}){return <Card className="card-hover p-5"><div className="flex items-start justify-between"><div><div className="text-sm text-[var(--muted-foreground)]">{label}</div><div className="mt-2 text-3xl font-black"><CountUp end={value} duration={1.1}/>{suffix}</div></div><span className="grid size-11 place-items-center rounded-2xl bg-emerald-500/10 text-emerald-500"><Icon className="size-5"/></span></div>{trend&&<div className="mt-4 text-xs font-semibold text-[var(--muted-foreground)]">{trend}</div>}</Card>}
