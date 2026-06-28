import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import KpiCard from "../components/KpiCard";
import UnknownCostBadge from "../components/UnknownCostBadge";

describe("KpiCard", () => {
  it("renders label and value", () => {
    render(<KpiCard label="Sessions" value="42" />);
    expect(screen.getByText("Sessions")).toBeInTheDocument();
    expect(screen.getByText("42")).toBeInTheDocument();
  });

  it("badge appears only when cost unknown", () => {
    const { container, rerender } = render(<UnknownCostBadge known={true} />);
    expect(container).toBeEmptyDOMElement();
    rerender(<UnknownCostBadge known={false} />);
    expect(screen.getByText(/coût incomplet/i)).toBeInTheDocument();
  });
});
