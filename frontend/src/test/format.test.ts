import { describe, expect, it } from "vitest";

import {
  formatCost, formatDuration, formatPercent, formatProjectName, formatTokens, mapToBarItems,
} from "../lib/format";

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

  it("shortens project slugs", () => {
    expect(formatProjectName("-home-vemore-workspace-ccdashboard")).toBe("ccdashboard");
    expect(formatProjectName("-home-vemore-workspace-ccdashboard-server")).toBe("ccdashboard-server");
    expect(formatProjectName("plain")).toBe("plain");
  });

  it("formats percentages", () => {
    expect(formatPercent(0.1234, 1)).toBe("12.3%");
    expect(formatPercent(Infinity)).toBe("—");
  });
});

describe("mapToBarItems", () => {
  it("converts a Record to sorted BarItem array", () => {
    expect(mapToBarItems({ TypeScript: 10, Python: 30, Rust: 5 })).toEqual([
      { label: "Python", value: 30 },
      { label: "TypeScript", value: 10 },
      { label: "Rust", value: 5 },
    ]);
  });

  it("returns an empty array for an empty map", () => {
    expect(mapToBarItems({})).toEqual([]);
  });

  it("respects the limit parameter", () => {
    const map: Record<string, number> = {};
    for (let i = 0; i < 20; i++) map[`lang${i}`] = i;
    const items = mapToBarItems(map, 5);
    expect(items).toHaveLength(5);
    expect(items[0].value).toBe(19);
    expect(items[4].value).toBe(15);
  });

  it("defaults to limit 12", () => {
    const map: Record<string, number> = {};
    for (let i = 0; i < 20; i++) map[`lang${i}`] = i;
    expect(mapToBarItems(map)).toHaveLength(12);
  });
});
