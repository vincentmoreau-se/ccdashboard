import type { Usage } from "../api/client";
import { formatCost, formatPercent, formatTokens } from "../lib/format";
import { theme } from "../theme";
import CountUp from "./CountUp";
import Donut from "./Donut";
import Panel from "./Panel";

/**
 * The headline "aha": Claude's prompt caching reads tokens at ~10× lower cost.
 * Shows where tokens come from, the cache hit rate, and the money it saved.
 */
export default function CacheSavingsCard({
  usage,
  savings,
  currency,
}: {
  usage: Usage;
  savings: number;
  currency: string;
}) {
  const cacheWrite = usage.cache_write_5m + usage.cache_write_1h;
  const slices = [
    { name: "Cache lu", value: usage.cache_read, color: theme.colors.green },
    { name: "Input (frais)", value: usage.input, color: theme.colors.accent },
    { name: "Output", value: usage.output, color: theme.colors.amber },
    { name: "Écriture cache", value: cacheWrite, color: theme.chart[3] },
  ];
  const denom = usage.cache_read + usage.input;
  const hitRate = denom > 0 ? usage.cache_read / denom : 0;

  return (
    <Panel
      title="Cache & économies"
      right="Le cache de prompt facture la relecture ~10× moins cher"
    >
      <div style={{ display: "flex", gap: 28, flexWrap: "wrap", alignItems: "center" }}>
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            gap: 4,
            minWidth: 180,
          }}
        >
          <div style={{ fontSize: 12.5, color: theme.colors.textMuted, textTransform: "uppercase", letterSpacing: "0.05em" }}>
            Économisé grâce au cache
          </div>
          <div
            style={{
              fontFamily: theme.font.mono,
              fontSize: 40,
              fontWeight: 600,
              lineHeight: 1.1,
              color: theme.colors.green,
            }}
          >
            <CountUp value={savings} format={(n) => formatCost(n, currency, true)} />
          </div>
          <div style={{ fontSize: 13, color: theme.colors.textMuted }}>
            Taux de hit cache : <strong style={{ color: theme.colors.text }}>{formatPercent(hitRate, 1)}</strong>
          </div>
          <div style={{ fontSize: 13, color: theme.colors.textMuted, fontFamily: theme.font.mono }}>
            {formatTokens(usage.cache_read)} tokens relus
          </div>
        </div>

        <div style={{ flex: 1, minWidth: 280 }}>
          <Donut
            data={slices}
            height={190}
            centerValue={formatPercent(hitRate, 0)}
            centerLabel="cache"
            formatValue={(n) => formatTokens(n)}
          />
        </div>
      </div>
    </Panel>
  );
}
