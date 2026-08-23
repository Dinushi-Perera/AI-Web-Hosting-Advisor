"use client";

import Link from "next/link";
import { useState } from "react";
import { CheckCircle2, Loader2, Mail } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { authService } from "@/services/auth-service";

const message=(error:unknown)=>error&&typeof error==="object"&&"message" in error?String(error.message):"The reset email could not be sent.";

export default function Forgot(){
  const [email,setEmail]=useState("");
  const [busy,setBusy]=useState(false);
  const [sent,setSent]=useState(false);
  const submit=async(event:React.FormEvent)=>{event.preventDefault();setBusy(true);try{const result=await authService.forgotPassword(email.trim());setSent(true);toast.success(result.message)}catch(error){toast.error(message(error))}finally{setBusy(false)}};
  return <div><Mail className="mb-5 size-10 text-emerald-500"/><h1 className="text-3xl font-black">Reset your password</h1>{sent?<div className="mt-5 rounded-2xl border border-green-500/20 bg-green-500/5 p-5"><CheckCircle2 className="size-7 text-green-600"/><h2 className="mt-3 font-black">Check your email</h2><p className="mt-1 text-sm text-[var(--muted-foreground)]">If an account exists for <strong>{email}</strong>, a reset link has been sent. The link expires after 30 minutes and can be used once.</p><Button className="mt-4" variant="outline" onClick={()=>setSent(false)}>Send another link</Button></div>:<><p className="mt-2 text-sm text-[var(--muted-foreground)]">Enter the email address you registered with. We will email you a secure password-reset link.</p><form onSubmit={submit} className="mt-6 grid gap-4"><Input required type="email" autoComplete="email" value={email} onChange={event=>setEmail(event.target.value)} placeholder="you@example.com"/><Button type="submit" disabled={busy} variant="gradient" size="lg">{busy?<Loader2 className="size-4 animate-spin"/>:<Mail className="size-4"/>}Send Reset Link</Button></form></>}<Button asChild variant="ghost" className="mt-3"><Link href="/login">Back to Sign In</Link></Button></div>;
}
