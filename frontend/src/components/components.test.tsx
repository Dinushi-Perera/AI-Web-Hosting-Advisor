import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { ScoreRing } from "@/components/shared/score-ring";
import { StatusBadge } from "@/components/shared/status-badge";
import { Button } from "@/components/ui/button";

describe("shared frontend components", () => {
  it("renders and invokes an accessible button", () => {
    const onClick = vi.fn();
    render(<Button onClick={onClick}>Start analysis</Button>);
    fireEvent.click(screen.getByRole("button", { name: "Start analysis" }));
    expect(onClick).toHaveBeenCalledOnce();
  });

  it("renders score values and labels", () => {
    render(<ScoreRing value={92} suffix="%" label="Performance" />);
    expect(screen.getByText("92%")).toBeDefined();
    expect(screen.getByText("Performance")).toBeDefined();
  });

  it.each(["Complete", "Failed", "Running", "Queued"])("renders the %s status", (status) => {
    render(<StatusBadge status={status} />);
    expect(screen.getByText(status)).toBeDefined();
  });
});
