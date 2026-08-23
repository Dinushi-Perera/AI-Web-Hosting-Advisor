"use client";

import { Area, AreaChart, Bar, BarChart, CartesianGrid, Cell, Legend, Line, LineChart, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

type PerformancePoint={date:string;performance:number|null};
type CostPoint={label:string;current?:number|null;recommended?:number|null};

export function PerformanceChart({data=[]}:{data?:PerformancePoint[]}){return data.length?<div className="h-72"><ResponsiveContainer width="100%" height="100%"><LineChart data={data.map(x=>({...x,date:new Date(x.date).toLocaleDateString()}))}><CartesianGrid strokeDasharray="3 3" opacity={.18}/><XAxis dataKey="date" tickLine={false} axisLine={false}/><YAxis domain={[0,100]} tickLine={false} axisLine={false}/><Tooltip/><Line type="monotone" dataKey="performance" stroke="#047857" strokeWidth={3} dot={{r:4}}/></LineChart></ResponsiveContainer></div>:<EmptyChart/>}

export function CostChart({data=[]}:{data?:CostPoint[]}){return data.length?<div className="h-72"><ResponsiveContainer width="100%" height="100%"><AreaChart data={data}><defs><linearGradient id="costFill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#d97706" stopOpacity={.35}/><stop offset="100%" stopColor="#d97706" stopOpacity={0}/></linearGradient></defs><CartesianGrid strokeDasharray="3 3" opacity={.18}/><XAxis dataKey="label" tickLine={false} axisLine={false}/><YAxis tickLine={false} axisLine={false}/><Tooltip/><Area type="monotone" dataKey="current" stroke="#d97706" fill="url(#costFill)" strokeWidth={2}/><Area type="monotone" dataKey="recommended" stroke="#22c55e" fillOpacity={0} strokeWidth={2}/></AreaChart></ResponsiveContainer></div>:<EmptyChart text="Cost history becomes available when projects include current hosting costs."/>}

export function HostingDistribution({data}:{data?:Record<string,number>}){const colors=["#f59e0b","#047857","#ea580c"];const rows=Object.entries(data??{}).filter(([,value])=>value>0).map(([name,value],i)=>({name:name.replaceAll("_"," "),value,color:colors[i%colors.length]}));return rows.length?<div className="h-72"><ResponsiveContainer width="100%" height="100%"><PieChart><Pie data={rows} dataKey="value" nameKey="name" innerRadius={62} outerRadius={90} paddingAngle={3}>{rows.map(v=><Cell key={v.name} fill={v.color}/>)}</Pie><Tooltip/><Legend/></PieChart></ResponsiveContainer></div>:<EmptyChart text="No completed recommendations yet."/>}

export function WorkloadChart({average=0,peak=0}:{average?:number;peak?:number}){const data=[{stage:"Average",requests:average},{stage:"Business peak",requests:peak},{stage:"Growth +30%",requests:Math.round(peak*1.3)}];return <div className="h-72"><ResponsiveContainer width="100%" height="100%"><BarChart data={data}><CartesianGrid strokeDasharray="3 3" opacity={.18}/><XAxis dataKey="stage" tickLine={false} axisLine={false}/><YAxis tickLine={false} axisLine={false}/><Tooltip/><Bar dataKey="requests" fill="#047857" radius={[8,8,0,0]}/></BarChart></ResponsiveContainer></div>}

function EmptyChart({text="No performance history yet."}:{text?:string}){return <div className="grid h-72 place-items-center rounded-xl border border-dashed text-center text-sm text-[var(--muted-foreground)]">{text}</div>}
