import {
  Bar, CartesianGrid, ComposedChart, Legend, Line, ResponsiveContainer,
  Tooltip, XAxis, YAxis,
} from "recharts";

import type { TimeBucket } from "../api/client";
import { theme } from "../theme";

export default function CostTokenChart({ data }: { data: TimeBucket[] }) {
  const rows = data.map((b) => ({
    date: b.date,
    cost: Number(b.cost.toFixed(2)),
    tokens: b.usage.input + b.usage.output,
  }));
  const axis = { stroke: theme.colors.border, tick: { fill: theme.colors.textMuted, fontSize: 11, fontFamily: theme.font.mono } };
  return (
    <ResponsiveContainer width="100%" height={280}>
      <ComposedChart data={rows} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
        <defs>
          <linearGradient id="tokensFill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={theme.colors.accent} stopOpacity={0.95} />
            <stop offset="100%" stopColor={theme.colors.accent} stopOpacity={0.35} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke={theme.colors.border} vertical={false} />
        <XAxis dataKey="date" {...axis} tickLine={false} axisLine={{ stroke: theme.colors.border }} />
        <YAxis yAxisId="left" {...axis} tickLine={false} axisLine={false} width={48} />
        <YAxis yAxisId="right" orientation="right" {...axis} tickLine={false} axisLine={false} width={48} />
        <Tooltip
          cursor={{ fill: "rgba(255,255,255,0.04)" }}
          contentStyle={{
            background: theme.colors.bgElevated,
            border: `1px solid ${theme.colors.borderStrong}`,
            borderRadius: theme.radius.sm,
            fontFamily: theme.font.mono,
            fontSize: 12,
            color: theme.colors.text,
            boxShadow: theme.shadow.card,
          }}
          labelStyle={{ color: theme.colors.textMuted, marginBottom: 4 }}
          itemStyle={{ padding: 0 }}
        />
        <Legend wrapperStyle={{ fontFamily: theme.font.body, fontSize: 12, color: theme.colors.textMuted, paddingTop: 8 }} />
        <Bar yAxisId="left" dataKey="tokens" name="Tokens" fill="url(#tokensFill)" radius={[3, 3, 0, 0]} maxBarSize={42} isAnimationActive={false} />
        <Line yAxisId="right" dataKey="cost" name="Coût" stroke={theme.colors.amber} strokeWidth={2} dot={{ r: 2.5, fill: theme.colors.amber, strokeWidth: 0 }} activeDot={{ r: 4 }} isAnimationActive={false} />
      </ComposedChart>
    </ResponsiveContainer>
  );
}
