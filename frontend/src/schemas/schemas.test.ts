import { describe, expect, it } from "vitest";

import { liveAnalysisSchema } from "./analysis";
import { loginSchema, registerSchema } from "./auth";

const validAnalysis = {
  projectName: "Advisor production site",
  websiteUrl: "https://example.com",
  category: "SaaS",
  monthlyVisitors: "10000",
  concurrentUsers: "100",
  growth: "Medium",
  trafficPattern: "Normal",
  budget: "150",
  budgetFlexibility: "Flexible",
  managesServers: true,
  highAvailability: true,
  rapidScaling: false,
  kubernetesSkill: false,
  managedDatabase: true,
  backups: true,
};

describe("authentication schemas", () => {
  it("normalizes valid login email input", () => {
    expect(loginSchema.parse({ email: "  user@example.com ", password: "Password1!" }).email).toBe("user@example.com");
  });

  it("rejects malformed email addresses and weak passwords", () => {
    expect(loginSchema.safeParse({ email: "not-an-email", password: "short" }).success).toBe(false);
    expect(registerSchema.safeParse({ fullName: "Test User", email: "user@example.com", password: "password", confirmPassword: "password" }).success).toBe(false);
  });

  it("rejects mismatched registration passwords", () => {
    const result = registerSchema.safeParse({ fullName: "Test User", email: "user@example.com", password: "StrongPass1!", confirmPassword: "Different1!" });
    expect(result.success).toBe(false);
  });
});

describe("live-analysis schema", () => {
  it("coerces numeric form fields", () => {
    const parsed = liveAnalysisSchema.parse(validAnalysis);
    expect(parsed.monthlyVisitors).toBe(10000);
    expect(parsed.concurrentUsers).toBe(100);
    expect(parsed.budget).toBe(150);
  });

  it.each(["http://localhost:3000", "http://127.0.0.1", "http://192.168.1.10", "ftp://example.com"])("rejects unsafe URL %s", (websiteUrl) => {
    expect(liveAnalysisSchema.safeParse({ ...validAnalysis, websiteUrl }).success).toBe(false);
  });

  it("accepts a public HTTPS URL", () => {
    expect(liveAnalysisSchema.safeParse(validAnalysis).success).toBe(true);
  });
});
