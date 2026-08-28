import { Activity, Chart, DocumentText, DollarCircle, Home, Layers, Microscope, ShieldTick, TestTube2, User } from "reicon-react";

export const navGroups = [
  { label: "Workspace", items: [
    { label: "Overview", href: "/dashboard", icon: Home },
    { label: "Projects", href: "/projects", icon: Layers },
    { label: "New Analysis", href: "/projects/new", icon: Microscope },
  ]},
  { label: "AI Advisor", items: [
    { label: "Performance Analysis", href: "/performance", icon: Chart },
    { label: "Load Testing", href: "/load-testing", icon: Activity },
    { label: "Cost Explorer", href: "/cost", icon: DollarCircle },
  ]},
  { label: "Reports & Testing", items: [
    { label: "Reports", href: "/reports", icon: DocumentText },
    { label: "Testing", href: "/testing", icon: TestTube2 },
  ]},
  { label: "Account", items: [
    { label: "Profile", href: "/settings/profile", icon: User },
    { label: "Security", href: "/settings/security", icon: ShieldTick },
  ]},
];
