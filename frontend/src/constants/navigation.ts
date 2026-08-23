import { CircleDollarSign, FileText, Home, Layers3, Microscope, ShieldCheck, TestTube2, User } from "lucide-react";

export const navGroups = [
  { label: "Workspace", items: [
    { label: "Overview", href: "/dashboard", icon: Home },
    { label: "Projects", href: "/projects", icon: Layers3 },
    { label: "New Analysis", href: "/projects/new", icon: Microscope },
  ]},
  { label: "AI Advisor", items: [
    { label: "Cost Explorer", href: "/cost", icon: CircleDollarSign },
  ]},
  { label: "Reports & Testing", items: [
    { label: "Reports", href: "/reports", icon: FileText },
    { label: "Testing", href: "/testing", icon: TestTube2 },
  ]},
  { label: "Account", items: [
    { label: "Profile", href: "/settings/profile", icon: User },
    { label: "Security", href: "/settings/security", icon: ShieldCheck },
  ]},
];
