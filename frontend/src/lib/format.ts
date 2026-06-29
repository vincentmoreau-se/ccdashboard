import type { CostBreakdown } from "../api/client";

export function formatTokens(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(2)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}k`;
  return String(n);
}

export function formatCost(n: number, currency: string, known: boolean): string {
  if (!known) return "n/a";
  return `${n.toFixed(2)} ${currency}`;
}

// Multi-line hover text (native title=) detailing what drives a cost. Cache tokens
// are excluded from the displayed token count but dominate the cost, so this makes
// an otherwise-surprising figure legible. Returns "" when the breakdown is absent.
export function costBreakdownTitle(
  bd: CostBreakdown | undefined,
  currency: string,
): string {
  if (!bd) return "";
  const line = (label: string, v: number) => `${label}: ${v.toFixed(2)} ${currency}`;
  return [
    line("Input", bd.input),
    line("Output", bd.output),
    line("Écriture cache", bd.cache_write),
    line("Lecture cache", bd.cache_read),
  ].join("\n");
}

export function formatDuration(seconds: number | null): string {
  if (seconds == null) return "—";
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  if (m >= 60) return `${Math.floor(m / 60)}h${m % 60}m`;
  return `${m}m${s}s`;
}

// Claude Code session dirs encode the cwd as a slug, e.g.
// "-home-vemore-workspace-ccdashboard" -> show just "ccdashboard".
export function formatProjectName(name: string): string {
  const cleaned = name.replace(/^-+/, "");
  const parts = cleaned.split("-").filter(Boolean);
  const tail = parts.slice(-1)[0] ?? name;
  // Re-glue a trailing "-server"/"-app"-like segment if the slug had several words
  // after the workspace root; heuristic: keep the last segment after "workspace".
  const wsIdx = parts.lastIndexOf("workspace");
  if (wsIdx >= 0 && wsIdx < parts.length - 1) return parts.slice(wsIdx + 1).join("-");
  return tail;
}

// "claude-opus-4-8" -> "Opus 4.8"; unknown / "(none)" pass through unchanged.
export function formatModel(model: string): string {
  const m = model.toLowerCase();
  const fam = m.includes("opus")
    ? "Opus"
    : m.includes("sonnet")
      ? "Sonnet"
      : m.includes("haiku")
        ? "Haiku"
        : null;
  if (!fam) return model;
  const ver = model.match(/(\d+)-(\d+)/);
  return ver ? `${fam} ${ver[1]}.${ver[2]}` : fam;
}

export function formatPercent(fraction: number, digits = 0): string {
  if (!isFinite(fraction)) return "—";
  return `${(fraction * 100).toFixed(digits)}%`;
}

export function formatCount(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}k`;
  return String(n);
}

/** Convert a Record<string, number> map to sorted BarList items, top N. */
export function mapToBarItems(
  map: Record<string, number>,
  limit = 12,
): { label: string; value: number }[] {
  return Object.entries(map)
    .map(([label, value]) => ({ label, value }))
    .sort((a, b) => b.value - a.value)
    .slice(0, limit);
}
