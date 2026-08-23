"use client";
import { WifiOff } from "lucide-react";
import { useOnlineStatus } from "@/hooks/use-online-status";
export function OfflineBanner(){const online=useOnlineStatus();if(online)return null;return <div className="flex items-center justify-center gap-2 bg-amber-500 px-4 py-2 text-center text-xs font-bold text-black"><WifiOff className="size-4"/>You&apos;re offline. Some analysis features are unavailable.</div>}
