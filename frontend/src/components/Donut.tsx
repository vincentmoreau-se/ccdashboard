import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";

import { theme } from "../theme";

export interface DonutSlice {
  name: string;
  value: number;
  color?: string;
}

/** Donut chart with a legend and an optional centered label. */
export default function Donut({
  data,
  height = 200,
  centerValue,
  centerLabel,
  formatValue = (n) => String(n),
}: {
  data: DonutSlice[];
  height?: number;
  centerValue?: string;
  centerLabel?: string;
  formatValue?: (n: number) => string;
}) {
  const total = data.reduce((a, s) => a + s.value, 0);
  const slices = data.filter((s) => s.value > 0);
  const center = centerValue;
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 18, flexWrap: "wrap" }}>
      <div style={{ position: "relative", width: height, height }}>
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={slices}
              dataKey="value"
              nameKey="name"
              cx="50%"
              cy="50%"
              innerRadius="62%"
              outerRadius="100%"
              paddingAngle={slices.length > 1 ? 2 : 0}
              stroke="none"
              isAnimationActive={false}
            >
              {slices.map((s, i) => (
                <Cell key={s.name} fill={s.color ?? theme.chart[i % theme.chart.length]} />
              ))}
            </Pie>
            <Tooltip
              contentStyle={{
                background: theme.colors.bgElevated,
                border: `1px solid ${theme.colors.borderStrong}`,
                borderRadius: theme.radius.sm,
                fontFamily: theme.font.mono,
                fontSize: 12,
                color: theme.colors.text,
              }}
              itemStyle={{ color: theme.colors.text }}
              labelStyle={{ color: theme.colors.textMuted }}
              formatter={(v: number, n: string) => [formatValue(v), n]}
            />
          </PieChart>
        </ResponsiveContainer>
        {(center || centerLabel) && (
          <div
            style={{
              position: "absolute",
              inset: 0,
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              justifyContent: "center",
              pointerEvents: "none",
            }}
          >
            {center && (
              <div style={{ fontFamily: theme.font.mono, fontSize: 19, fontWeight: 600, color: theme.colors.text }}>
                {center}
              </div>
            )}
            {centerLabel && (
              <div style={{ fontSize: 11, color: theme.colors.textMuted, textTransform: "uppercase", letterSpacing: "0.05em" }}>
                {centerLabel}
              </div>
            )}
          </div>
        )}
      </div>

      <ul style={{ listStyle: "none", margin: 0, padding: 0, display: "grid", gap: 7, minWidth: 150 }}>
        {data.map((s, i) => (
          <li key={s.name} style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 13 }}>
            <span
              style={{
                width: 10,
                height: 10,
                borderRadius: 3,
                background: s.color ?? theme.chart[i % theme.chart.length],
                flexShrink: 0,
              }}
            />
            <span style={{ color: theme.colors.textMuted, flex: 1 }}>{s.name}</span>
            <span style={{ fontFamily: theme.font.mono, color: theme.colors.text }}>{formatValue(s.value)}</span>
            <span style={{ fontFamily: theme.font.mono, color: theme.colors.textFaint, fontSize: 11, width: 42, textAlign: "right" }}>
              {total > 0 ? `${((s.value / total) * 100).toFixed(0)}%` : "—"}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}
