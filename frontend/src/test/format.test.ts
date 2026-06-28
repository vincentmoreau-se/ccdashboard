import { describe, expect, it } from "vitest";

import { formatCost, formatDuration, formatTokens } from "../lib/format";

describe("format", () => {
  it("formats tokens", () => {
    expect(formatTokens(500)).toBe("500");
    expect(formatTokens(1500)).toBe("1.5k");
    expect(formatTokens(2_000_000)).toBe("2.00M");
  });

  it("formats cost with unknown flag", () => {
    expect(formatCost(1.5, "€", true)).toBe("1.50 €");
    expect(formatCost(1.5, "€", false)).toBe("n/a");
  });

  it("formats duration", () => {
    expect(formatDuration(null)).toBe("—");
    expect(formatDuration(125)).toBe("2m5s");
  });
});
