"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft, ArrowRight, Check, Loader2, Sparkles } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { userService } from "@/services/user-service";

const steps=["Welcome","Experience","Region","Ready"];

export default function Onboarding(){
  const [step,setStep]=useState(0);const [experience,setExperience]=useState("Beginner");const [region,setRegion]=useState("Sri Lanka");const [busy,setBusy]=useState(false);const router=useRouter();
  const finish=async(destination:string)=>{setBusy(true);try{await userService.update({experienceLevel:experience as "Beginner"|"Intermediate"|"Advanced",defaultRegion:region});const current=await userService.preferences();await userService.updatePreferences({...current,defaultRegion:region,onboardingCompleted:true});toast.success("Profile setup saved");router.push(destination)}catch(e){toast.error(e&&typeof e==="object"&&"message" in e?String(e.message):"Could not save profile setup")}finally{setBusy(false)}};
  return <div className="mx-auto max-w-3xl py-8"><div className="mb-8"><div className="flex items-center justify-between text-xs font-bold text-[var(--muted-foreground)]"><span>Step {step+1} of {steps.length}</span></div><Progress value={(step+1)/steps.length*100} className="mt-3"/></div><Card className="overflow-hidden"><div className="h-2 bg-gradient-to-r from-emerald-500 via-emerald-500 to-amber-500"/><CardContent className="p-6 md:p-10">{step===0&&<Panel icon={<Sparkles/>} title="Welcome to your AI Hosting Advisor" text="Choose the account defaults that will be saved for future analyses."/>}{step===1&&<ChoicePanel title="How comfortable are you with web infrastructure?" value={experience} setValue={setExperience} options={["Beginner","Intermediate","Advanced"]}/>} {step===2&&<ChoicePanel title="Default analysis region" value={region} setValue={setRegion} options={["Sri Lanka","Singapore","Mumbai","London","Frankfurt","Sydney","New York"]}/>} {step===3&&<Panel icon={<Check/>} title="You are ready" text={`${experience} experience · ${region} region · USD currency.`}/>}<div className="mt-8 flex justify-between"><Button variant="ghost" disabled={step===0||busy} onClick={()=>setStep(s=>s-1)}><ArrowLeft className="size-4"/>Back</Button>{step<steps.length-1?<Button variant="gradient" onClick={()=>setStep(s=>s+1)}>Continue<ArrowRight className="size-4"/></Button>:<div className="flex gap-2"><Button variant="outline" disabled={busy} onClick={()=>finish("/dashboard")}>{busy?<Loader2 className="size-4 animate-spin"/>:null}Go to Dashboard</Button><Button variant="gradient" disabled={busy} onClick={()=>finish("/projects/new")}>Start First Analysis</Button></div>}</div></CardContent></Card></div>;
}

function Panel({icon,title,text}:{icon:React.ReactNode;title:string;text:string}){return <div className="py-8 text-center"><div className="mx-auto grid size-16 place-items-center rounded-3xl bg-emerald-500/10 text-emerald-500">{icon}</div><h1 className="mt-6 text-3xl font-black">{title}</h1><p className="mx-auto mt-3 max-w-xl text-[var(--muted-foreground)]">{text}</p></div>}
function ChoicePanel({title,value,setValue,options}:{title:string;value:string;setValue:(value:string)=>void;options:string[]}){return <div><h1 className="text-2xl font-black">{title}</h1><div className="mt-6 grid gap-3 sm:grid-cols-2">{options.map(option=><button key={option} onClick={()=>setValue(option)} className={`rounded-2xl border p-5 text-left font-bold ${value===option?"border-emerald-500 bg-emerald-500/10":"hover:bg-[var(--muted)]"}`}>{option}</button>)}</div></div>}
