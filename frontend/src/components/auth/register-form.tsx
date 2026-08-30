"use client";

import Link from "next/link";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm, useWatch } from "react-hook-form";
import { z } from "zod";
import { CheckCircle2, Eye, EyeOff, Loader2, UserPlus } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Field } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { registerSchema } from "@/schemas/auth";
import { authService } from "@/services/auth-service";

type Values=z.infer<typeof registerSchema>;
const errorMessage=(error:unknown)=>error&&typeof error==="object"&&"message" in error?String(error.message):"Account creation failed. Please try again.";
const errorCode=(error:unknown)=>error&&typeof error==="object"&&"code" in error?String(error.code):undefined;

export function RegisterForm(){
  const router=useRouter();
  const [show,setShow]=useState(false);
  const form=useForm<Values>({resolver:zodResolver(registerSchema),defaultValues:{fullName:"",email:"",password:"",confirmPassword:""}});
  const password=useWatch({control:form.control,name:"password"})||"";
  const rules=[["8+ characters",password.length>=8],["uppercase",/[A-Z]/.test(password)],["lowercase",/[a-z]/.test(password)],["number",/[0-9]/.test(password)],["special character",/[^A-Za-z0-9]/.test(password)]] as const;
  const submit=async(values:Values)=>{try{const result=await authService.register({fullName:values.fullName,email:values.email,password:values.password});toast.success(result.message||"Registration successful. You are now signed in.",{duration:5000});router.replace("/onboarding")}catch(error){const message=errorMessage(error);if(errorCode(error)==="AUTH_EMAIL_EXISTS")form.setError("email",{type:"server",message});toast.error(message)}};
  return <form onSubmit={form.handleSubmit(submit)} className="grid gap-4">
    <Field label="Full Name" error={form.formState.errors.fullName?.message}><Input autoComplete="name" placeholder="Sarah Perera" {...form.register("fullName")}/></Field>
    <Field label="Email" error={form.formState.errors.email?.message}><Input type="email" autoComplete="email" placeholder="you@example.com" {...form.register("email")}/></Field>
    <Field label="Password" error={form.formState.errors.password?.message}><div className="relative"><Input type={show?"text":"password"} autoComplete="new-password" {...form.register("password")}/><button type="button" onClick={()=>setShow(!show)} className="absolute right-3 top-3 text-[var(--muted-foreground)]" aria-label={show?"Hide password":"Show password"}>{show?<EyeOff className="size-4"/>:<Eye className="size-4"/>}</button></div></Field>
    <div className="grid grid-cols-2 gap-2">{rules.map(([label,valid])=><div key={label} className={`flex items-center gap-1.5 text-xs ${valid?"text-green-600":"text-[var(--muted-foreground)]"}`}><CheckCircle2 className="size-3.5"/>{label}</div>)}</div>
    <Field label="Confirm Password" error={form.formState.errors.confirmPassword?.message}><Input type="password" autoComplete="new-password" {...form.register("confirmPassword")}/></Field>
    <Button type="submit" variant="gradient" size="lg" disabled={form.formState.isSubmitting}>{form.formState.isSubmitting?<><Loader2 className="size-4 animate-spin"/>Creating account...</>:<><UserPlus className="size-4"/>Create Account</>}</Button>
    <div className="text-center text-sm text-[var(--muted-foreground)]">Already registered? <Link className="font-bold text-emerald-500" href="/login">Sign in</Link></div>
  </form>;
}
