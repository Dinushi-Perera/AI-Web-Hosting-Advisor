export type ProjectMode = "LIVE" | "PLANNED" | "IDEA";
export type ProjectStatus = "Draft" | "Queued" | "Analysing" | "Completed" | "Needs Attention" | "Failed" | "Cancelled" | "Archived";
export type ConfidenceStatus = "High Confidence" | "Medium Confidence" | "Low Confidence" | "Insufficient Data";

export interface User {
  id: string;
  fullName: string;
  email: string;
  role: "user";
  experienceLevel: "Beginner" | "Intermediate" | "Advanced";
  defaultRegion: string;
  currency: string;
  timezone: string;
  avatar?: string | null;
  avatarUrl?: string | null;
}

export interface Project {
  id: string;
  name: string;
  mode: ProjectMode;
  website?: string;
  status: ProjectStatus;
  performanceScore?: number;
  recommendation?: "VPS" | "Cloud VM" | "Kubernetes";
  costRange?: [number, number];
  confidence?: number;
  updatedAt: string;
}

export interface TechnologyDetection {
  category: string;
  technology: string;
  confidence: number;
  evidence: string[];
  status: "High" | "Medium" | "Low" | "Unknown";
}

export interface CoreWebVitals {
  lcp?: number;
  inp?: number;
  cls?: number;
  fcp?: number;
  tbt?: number;
  speedIndex?: number;
}

export interface PerformanceAudit {
  performance?: number;
  accessibility?: number;
  bestPractices?: number;
  seo?: number;
  mobile?: CoreWebVitals;
  desktop?: CoreWebVitals;
}

export interface WorkloadEstimate {
  concurrentUsers?: number;
  requestsPerSecond?: number;
  peakRequests?: number;
  trafficClass?: "Low" | "Medium" | "High" | "Very High";
  databaseIntensity?: string;
  storageGb?: number;
  bandwidthGb?: number;
  growth?: string;
}

export interface InfrastructureOption {
  type: "VPS" | "Cloud VM" | "Kubernetes";
  fitScore: number;
  estimatedMonthlyRange: [number, number];
  scalability: string;
  complexity: string;
  maintenance: string;
  highAvailability: string;
  bestFor: string;
}

export interface HostingRecommendation {
  recommended: InfrastructureOption["type"];
  fitScore: number;
  confidence: number;
  reasons: Array<{ label: string; score: number; note: string }>;
  alternatives: InfrastructureOption[];
  resources: { vcpu: number; ramGb: number; storageGb: number; transferTb: number };
  assumptions: string[];
}

export interface PricingPlan {
  id: string;
  provider: string;
  plan: string;
  region: string;
  vcpu: number;
  ramGb: number;
  storageGb: number;
  monthlyRange: [number, number];
  updatedAt: string;
}

export interface OptimizationSuggestion {
  id: string;
  priority: "Critical" | "High" | "Medium" | "Low";
  category: string;
  title: string;
  explanation: string;
  impact: string;
  difficulty: "Easy" | "Medium" | "Hard";
  benefit: string;
  status: "Open" | "Done" | "Not Relevant";
}

export interface LoadTestPlan {
  testType: "Smoke" | "Load" | "Stress" | "Spike" | "Soak";
  virtualUsers: number;
  rampUpSeconds: number;
  durationSeconds: number;
  targetUrl: string;
  expectedResponseTimeMs: number;
  errorRateThreshold: number;
  stages: Array<{ duration: string; target: number }>;
  script: string;
}

export interface Report {
  id: string;
  projectId: string;
  generatedAt: string;
  status: string;
}

export interface APIError {
  message: string;
  code?: string;
  errorId?: string;
}
