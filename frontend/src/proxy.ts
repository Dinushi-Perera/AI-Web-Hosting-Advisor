import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const protectedPrefixes=["/dashboard","/projects","/analyze","/reports","/notifications","/settings","/testing","/cost","/demo-showcase"];

export function proxy(request:NextRequest){
  if(process.env.NEXT_PUBLIC_AUTH_REQUIRED==="false")return NextResponse.next();
  const protectedRoute=protectedPrefixes.some(prefix=>request.nextUrl.pathname.startsWith(prefix));
  if(!protectedRoute)return NextResponse.next();
  if(request.cookies.get("advisor_session")||request.cookies.get("advisor_refresh"))return NextResponse.next();
  const url=request.nextUrl.clone();
  url.pathname="/login";
  url.searchParams.set("returnTo",request.nextUrl.pathname);
  return NextResponse.redirect(url);
}

export const config={matcher:["/((?!_next/static|_next/image|favicon.ico).*)"]};
