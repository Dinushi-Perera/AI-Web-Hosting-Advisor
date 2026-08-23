import { z } from "zod";

const publicUrl = z.string().trim().url("Enter a valid public HTTP/HTTPS URL.").refine((value) => {
  try {
    const u = new URL(value);
    if (!['http:', 'https:'].includes(u.protocol)) return false;
    const host = u.hostname.toLowerCase();
    if (host === 'localhost' || host.endsWith('.local')) return false;
    if (/^(127\.|10\.|192\.168\.|169\.254\.)/.test(host)) return false;
    const m = host.match(/^172\.(\d+)\./);
    if (m && Number(m[1]) >= 16 && Number(m[1]) <= 31) return false;
    return true;
  } catch { return false; }
}, "Only public HTTP/HTTPS websites can be analysed.");

export const liveAnalysisSchema = z.object({
  projectName: z.string().trim().min(2).max(120),
  websiteUrl: publicUrl,
  category: z.string().min(1),
  region: z.string().min(1),
  monthlyVisitors: z.coerce.number<number>().int().min(0).max(1_000_000_000),
  concurrentUsers: z.coerce.number<number>().int().min(1, "Enter 1 to 1,000,000 concurrent users.").max(1_000_000),
  growth: z.string(),
  trafficPattern: z.string(),
  budget: z.coerce.number<number>().min(0).max(1_000_000),
  currency: z.string(),
  budgetFlexibility: z.string(),
  managesServers: z.boolean(),
  highAvailability: z.boolean(),
  rapidScaling: z.boolean(),
  kubernetesSkill: z.boolean(),
  managedDatabase: z.boolean(),
  backups: z.boolean(),
});

export type LiveAnalysisValues = z.infer<typeof liveAnalysisSchema>;
