"use client";

import { use, useEffect, useRef, useState } from "react";
import { redirect } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Camera, KeyRound, Loader2, Save, ShieldCheck, Trash2, UserCircle2 } from "lucide-react";
import { useTheme } from "next-themes";
import { toast } from "sonner";
import { PageHeader } from "@/components/shared/page-header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Field } from "@/components/ui/field";
import { Input, Select } from "@/components/ui/input";
import { userService } from "@/services/user-service";

const message = (error: unknown) => error && typeof error === "object" && "message" in error ? String(error.message) : "The request could not be completed.";

export default function SettingsPage({params}:{params:Promise<{section:string}>}) {
  const {section}=use(params);
  if(section==="profile") return <Profile/>;
  if(section==="security") return <Security/>;
  redirect("/settings/profile");
}

function Profile() {
  const queryClient=useQueryClient(); const fileRef=useRef<HTMLInputElement>(null); const [avatarVersion,setAvatarVersion]=useState(0);
  const profile=useQuery({queryKey:["profile"],queryFn:userService.me});
  const [form,setForm]=useState({fullName:"",email:"",experienceLevel:"Beginner",defaultRegion:"Sri Lanka",timezone:"Asia/Colombo"});
  useEffect(()=>{if(profile.data)setForm({fullName:profile.data.fullName,email:profile.data.email,experienceLevel:profile.data.experienceLevel,defaultRegion:profile.data.defaultRegion,timezone:profile.data.timezone})},[profile.data]);
  const save=useMutation({mutationFn:()=>userService.update({...form,experienceLevel:form.experienceLevel as "Beginner"|"Intermediate"|"Advanced",currency:"USD"}),onSuccess:(data)=>{queryClient.setQueryData(["profile"],data);toast.success("Profile saved to the database")},onError:(e)=>toast.error(message(e))});
  const upload=useMutation({mutationFn:(file:File)=>userService.uploadAvatar(file),onSuccess:()=>{setAvatarVersion(v=>v+1);queryClient.invalidateQueries({queryKey:["profile"]});toast.success("Profile image updated")},onError:(e)=>toast.error(message(e))});
  const remove=useMutation({mutationFn:userService.removeAvatar,onSuccess:()=>{setAvatarVersion(v=>v+1);queryClient.invalidateQueries({queryKey:["profile"]});toast.success("Profile image removed")},onError:(e)=>toast.error(message(e))});
  const reset=()=>{if(profile.data)setForm({fullName:profile.data.fullName,email:profile.data.email,experienceLevel:profile.data.experienceLevel,defaultRegion:profile.data.defaultRegion,timezone:profile.data.timezone})};
  if(profile.isLoading)return <Loading/>;
  if(profile.isError)return <ErrorState text={message(profile.error)} retry={()=>profile.refetch()}/>;
  return <div className="grid gap-6"><PageHeader eyebrow="Account" title="Profile" description="Your account details are loaded from and saved to the database."/><Card><CardContent className="grid gap-6 p-6 pt-6 lg:grid-cols-[220px_1fr]"><div className="text-center"><div className="mx-auto grid size-28 overflow-hidden place-items-center rounded-full bg-gradient-to-br from-emerald-500/15 to-amber-500/15">{profile.data?.avatar?<img key={avatarVersion} src={`${userService.avatarUrl()}?v=${avatarVersion}`} alt="Profile" className="size-full object-cover"/>:<UserCircle2 className="size-16 text-emerald-500"/>}</div><input ref={fileRef} type="file" accept="image/png,image/jpeg,image/webp" className="hidden" onChange={e=>{const f=e.target.files?.[0];if(f)upload.mutate(f);e.currentTarget.value=""}}/><div className="mt-4 flex justify-center gap-2"><Button size="sm" variant="outline" disabled={upload.isPending} onClick={()=>fileRef.current?.click()}><Camera className="size-4"/>{upload.isPending?"Uploading...":"Upload"}</Button>{profile.data?.avatar&&<Button size="sm" variant="ghost" disabled={remove.isPending} onClick={()=>remove.mutate()}><Trash2 className="size-4"/>Remove</Button>}</div><div className="mt-2 text-xs text-[var(--muted-foreground)]">JPG, PNG or WebP up to 2 MB</div></div><div className="grid gap-4 md:grid-cols-2"><Field label="Full Name"><Input value={form.fullName} onChange={e=>setForm({...form,fullName:e.target.value})}/></Field><Field label="Email"><Input type="email" value={form.email} onChange={e=>setForm({...form,email:e.target.value})}/></Field><Field label="Role"><Input value={profile.data?.role??"user"} disabled className="capitalize"/></Field><Field label="Experience Level"><Select value={form.experienceLevel} onChange={e=>setForm({...form,experienceLevel:e.target.value})}><option>Beginner</option><option>Intermediate</option><option>Advanced</option></Select></Field><Field label="Default Region"><Select value={form.defaultRegion} onChange={e=>setForm({...form,defaultRegion:e.target.value})}><option>London</option><option>Frankfurt</option><option>Singapore</option><option>Sri Lanka</option><option>Mumbai</option><option>Sydney</option><option>New York</option></Select></Field><Field label="Currency"><Input value="USD" disabled/></Field><Field label="Timezone"><Input value={form.timezone} onChange={e=>setForm({...form,timezone:e.target.value})}/></Field><div className="flex gap-2 md:col-span-2"><Button disabled={save.isPending||!form.fullName.trim()||!form.email.trim()} onClick={()=>save.mutate()}>{save.isPending?<Loader2 className="size-4 animate-spin"/>:<Save className="size-4"/>}Save Changes</Button><Button variant="ghost" onClick={reset}>Cancel</Button></div></div></CardContent></Card></div>;
}

function Security() {
  const queryClient=useQueryClient(); const sessions=useQuery({queryKey:["sessions"],queryFn:userService.sessions});
  const [current,setCurrent]=useState("");const [next,setNext]=useState("");const [confirm,setConfirm]=useState("");
  const change=useMutation({mutationFn:()=>userService.changePassword(current,next),onSuccess:()=>{setCurrent("");setNext("");setConfirm("");toast.success("Password updated in the database")},onError:(e)=>toast.error(message(e))});
  const revoke=useMutation({mutationFn:userService.revokeSession,onSuccess:()=>{queryClient.invalidateQueries({queryKey:["sessions"]});toast.success("Session revoked")},onError:(e)=>toast.error(message(e))});
  const revokeAll=useMutation({mutationFn:userService.revokeAllSessions,onSuccess:()=>{queryClient.invalidateQueries({queryKey:["sessions"]});toast.success("All sessions revoked. Sign in again if needed.")},onError:(e)=>toast.error(message(e))});
  const passwordValid=next.length>=8&&/[A-Z]/.test(next)&&/[a-z]/.test(next)&&/[0-9]/.test(next)&&/[^A-Za-z0-9]/.test(next)&&next===confirm;
  return <div className="grid gap-6"><PageHeader eyebrow="Account" title="Security" description="Change your password and revoke active database-backed sessions."/><div className="grid gap-4 lg:grid-cols-2"><Card><CardHeader><div className="flex items-center gap-2"><KeyRound className="size-5 text-emerald-500"/><CardTitle>Change Password</CardTitle></div></CardHeader><CardContent className="grid gap-4"><Field label="Current Password"><Input type="password" value={current} onChange={e=>setCurrent(e.target.value)}/></Field><Field label="New Password"><Input type="password" value={next} onChange={e=>setNext(e.target.value)}/></Field><Field label="Confirm New Password"><Input type="password" value={confirm} onChange={e=>setConfirm(e.target.value)}/></Field>{confirm&&next!==confirm&&<div className="text-xs text-[var(--danger)]">Passwords do not match.</div>}<Button disabled={change.isPending||!current||!passwordValid} onClick={()=>change.mutate()}>{change.isPending?<Loader2 className="size-4 animate-spin"/>:"Update Password"}</Button></CardContent></Card><Card><CardHeader><div className="flex items-center gap-2"><ShieldCheck className="size-5 text-emerald-500"/><CardTitle>Active Sessions</CardTitle></div></CardHeader><CardContent className="grid gap-3">{sessions.isLoading?<Loading/>:sessions.data?.length?sessions.data.map(session=><div key={session.id} className="rounded-xl border p-4"><div className="font-bold">{session.device||"Unknown device"}</div><div className="mt-1 text-xs text-[var(--muted-foreground)]">{session.ip||"IP unavailable"} · Last active {new Date(session.lastActive).toLocaleString()}</div><Button className="mt-3" variant="outline" size="sm" disabled={revoke.isPending} onClick={()=>revoke.mutate(session.id)}>Revoke session</Button></div>):<div className="text-sm text-[var(--muted-foreground)]">No active sessions.</div>}<Button variant="danger" disabled={revokeAll.isPending||!sessions.data?.length} onClick={()=>revokeAll.mutate()}>Revoke all sessions</Button></CardContent></Card></div></div>;
}

function Loading(){return <div className="grid min-h-48 place-items-center"><Loader2 className="size-6 animate-spin text-emerald-500"/></div>}
function ErrorState({text,retry}:{text:string;retry:()=>void}){return <div className="grid min-h-48 place-items-center rounded-2xl border"><div className="text-center"><p className="text-sm text-[var(--danger)]">{text}</p><Button className="mt-4" variant="outline" onClick={retry}>Try again</Button></div></div>}
