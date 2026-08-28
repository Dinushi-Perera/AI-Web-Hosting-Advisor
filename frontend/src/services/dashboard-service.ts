import { apiClient } from "./api-client";
import type { Project } from "@/types/domain";

export type DashboardData={
  summary:{total_projects:number;completed_analyses:number;average_performance_score:number|null;estimated_monthly_savings:number|null;reports_generated:number;high_priority_issues:number;currency:"USD"};
  recent_projects:Project[];
  performance_trend:Array<{date:string;performance:number|null;project_id:string}>;
  cost_trend:Array<{id:string;recorded_at:string;project_id:string;project_name:string;current:number|null;recommended:number;recommended_min:number|null;recommended_max:number|null;currency:"USD"}>;
  cost_summary:{currency:"USD";points:number;note:string};
  hosting_distribution:Record<string,number>;
  priority_issues:number;
  recent_activity:Array<{id:string;action:string;projectId:string|null;projectTitle:string|null;timestamp:string;metadata:Record<string,unknown>}>;
};

export const dashboardService={get:()=>apiClient.get<DashboardData>("/dashboard").then(r=>r.data)};
