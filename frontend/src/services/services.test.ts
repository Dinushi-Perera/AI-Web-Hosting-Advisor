import { beforeEach, describe, expect, it, vi } from "vitest";

import { apiClient } from "./api-client";
import { analysisService } from "./analysis-service";
import { authService } from "./auth-service";
import { projectService } from "./project-service";
import { testingService } from "./testing-service";

vi.mock("./api-client", () => ({
  apiClient: { get: vi.fn(), post: vi.fn(), patch: vi.fn(), delete: vi.fn() },
}));

const response = { data: { success: true } };

describe("frontend API service contracts", () => {
  beforeEach(() => {
    vi.mocked(apiClient.get).mockResolvedValue(response);
    vi.mocked(apiClient.post).mockResolvedValue(response);
    vi.mocked(apiClient.patch).mockResolvedValue(response);
    vi.mocked(apiClient.delete).mockResolvedValue(response);
  });

  it("uses the authentication endpoints", async () => {
    await authService.login({ email: "user@example.com", password: "StrongPass1!" });
    await authService.me();
    expect(apiClient.post).toHaveBeenCalledWith("/auth/login", { email: "user@example.com", password: "StrongPass1!" });
    expect(apiClient.get).toHaveBeenCalledWith("/auth/me");
  });

  it("uses extended timeouts for analysis pipelines", async () => {
    const payload = { projectName: "Test" };
    await analysisService.startLive(payload);
    await analysisService.startPlanned(payload);
    expect(apiClient.post).toHaveBeenCalledWith("/analysis/live", payload, { timeout: 120_000 });
    expect(apiClient.post).toHaveBeenCalledWith("/analysis/planned", payload, { timeout: 120_000 });
  });

  it("encodes project IDs in project operations", async () => {
    await projectService.get("project-1");
    await projectService.update("project-1", { title: "Updated" });
    await projectService.remove("project-1");
    expect(apiClient.get).toHaveBeenCalledWith("/projects/project-1");
    expect(apiClient.patch).toHaveBeenCalledWith("/projects/project-1", { title: "Updated" });
    expect(apiClient.delete).toHaveBeenCalledWith("/projects/project-1");
  });

  it("passes optional testing filters only when supplied", async () => {
    await testingService.summary();
    await testingService.summary("project-1");
    expect(apiClient.get).toHaveBeenNthCalledWith(1, "/testing/summary", { params: undefined });
    expect(apiClient.get).toHaveBeenNthCalledWith(2, "/testing/summary", { params: { project_id: "project-1" } });
  });
});
