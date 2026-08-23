import { Sidebar } from "./sidebar";
import { Topbar } from "./topbar";
import { MobileNav } from "./mobile-nav";
import { OfflineBanner } from "./offline-banner";
export function AppShell({children}:{children:React.ReactNode}){return <div className="min-h-screen lg:flex"><Sidebar/><div className="min-w-0 flex-1"><OfflineBanner/><Topbar/><main id="main-content" className="mx-auto max-w-[1600px] p-4 pb-24 md:p-6 lg:pb-8">{children}</main><footer className="hidden border-t px-6 py-4 text-center text-xs text-[var(--muted-foreground)] lg:block">AI Web Hosting Advisor · v1.0 · Decision Support · Privacy · Terms</footer></div><MobileNav/></div>}
