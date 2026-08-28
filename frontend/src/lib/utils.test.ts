import { afterEach, describe, expect, it, vi } from "vitest";

import { cn, formatCurrency, greeting } from "./utils";

describe("frontend utilities", () => {
  afterEach(() => vi.useRealTimers());

  it("merges conditional and conflicting Tailwind classes", () => {
    expect(cn("px-2", false && "hidden", "px-4", "font-bold")).toBe("px-4 font-bold");
  });

  it("formats whole US-dollar values", () => {
    expect(formatCurrency(1234.49)).toMatch(/\$1,234/);
  });

  it.each([
    ["2026-08-28T08:00:00", "Good Morning"],
    ["2026-08-28T14:00:00", "Good Afternoon"],
    ["2026-08-28T20:00:00", "Good Evening"],
  ])("returns the expected greeting at %s", (time, expected) => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date(time));
    expect(greeting()).toBe(expected);
  });
});
