import axios from "axios";
import type { InternalAxiosRequestConfig } from "axios";

export const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1",
  withCredentials: true,
  timeout: 30_000,
  headers: { "Content-Type": "application/json" },
});

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const request = error?.config as (InternalAxiosRequestConfig & { _authRetry?: boolean }) | undefined;
    const path = String(request?.url ?? "");
    const canRefresh = error?.response?.status === 401 && request && !request._authRetry && !path.includes("/auth/login") && !path.includes("/auth/register") && !path.includes("/auth/refresh");
    if (canRefresh) {
      request._authRetry = true;
      try {
        await axios.post(`${apiClient.defaults.baseURL}/auth/refresh`, {}, { withCredentials: true });
        return apiClient.request(request);
      } catch {
        if (typeof window !== "undefined" && !window.location.pathname.startsWith("/login")) {
          // A full reload clears authenticated client state after refresh failure.
          // eslint-disable-next-line @next/next/no-location-assign-relative-destination
          window.location.assign(`/login?returnTo=${encodeURIComponent(window.location.pathname)}`);
        }
      }
    }
    const safeMessage = error?.response?.data?.message || "The request could not be completed.";
    return Promise.reject({ message: safeMessage, code: error?.response?.data?.code });
  },
);
