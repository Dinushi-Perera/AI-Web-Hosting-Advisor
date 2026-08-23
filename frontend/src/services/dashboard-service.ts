import { apiClient } from "./api-client";
import type { Project } from "@/types/domain";

export type DashboardData={
  summary:{total_projects:number;completed_analyses:number;average_performance_score:number|null;estimated_monthly_savings:number|null;reports_generated:number;high_priority_issues:number;currency:"USD"};
  recent_projects:Project[];
  performance_trend:Array<{date:string;performance:number|null;project_id:string}>;
  hosting_distribution:Record<string,number>;
  priority_issues:number;
};

export const dashboardService={get:()=>apiClient.get<DashboardData>("/dashboard").then(r=>r.data)};
