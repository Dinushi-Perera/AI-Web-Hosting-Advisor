"use client";
import Link from "next/link";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { Loader2, LogIn } from "lucide-react";
import { toast } from "sonner";
import { useRouter, useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Field } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { loginSchema } from "@/schemas/auth";
import { authService } from "@/services/auth-service";

type V=z.infer<typeof loginSchema>;
export function LoginForm(){const router=useRouter();const search=useSearchParams();const {register,handleSubmit,formState:{errors,isSubmitting}}=useForm<V>({resolver:zodResolver(loginSchema),defaultValues:{email:"",password:""}});const submit=async(v:V)=>{try{await authService.login(v);toast.success('Welcome back');router.push(search.get('returnTo')||'/dashboard')}catch{toast.error('Sign in failed. Check your email and password.')}};return <form onSubmit={handleSubmit(submit)} className="grid gap-4"><Field label="Email" error={errors.email?.message}><Input type="email" autoComplete="email" placeholder="you@example.com" {...register('email')}/></Field><Field label="Password" error={errors.password?.message}><Input type="password" autoComplete="current-password" placeholder="••••••••" {...register('password')}/></Field><Button type="submit" variant="gradient" size="lg" disabled={isSubmitting}>{isSubmitting?<><Loader2 className="size-4 animate-spin"/>Signing in...</>:<><LogIn className="size-4"/>Sign In</>}</Button><div className="text-center text-sm text-[var(--muted-foreground)]">New here? <Link className="font-bold text-emerald-500" href="/register">Create Account</Link></div></form>}
