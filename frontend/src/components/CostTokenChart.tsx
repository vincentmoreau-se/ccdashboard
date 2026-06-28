import {
  Bar, CartesianGrid, ComposedChart, Legend, Line, ResponsiveContainer,
  Tooltip, XAxis, YAxis,
} from "recharts";

import type { TimeBucket } from "../api/client";

export default function CostTokenChart({ data }: { data: TimeBucket[] }) {
  const rows = data.map((b) => ({
    date: b.date,
    cost: Number(b.cost.toFixed(2)),
    tokens: b.usage.input + b.usage.output,
  }));
  return (
    <ResponsiveContainer width="100%" height={280}>
      <ComposedChart data={rows}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="date" />
        <YAxis yAxisId="left" />
        <YAxis yAxisId="right" orientation="right" />
        <Tooltip />
        <Legend />
        <Bar yAxisId="left" dataKey="tokens" name="Tokens" fill="#93c5fd" isAnimationActive={false} />
        <Line yAxisId="right" dataKey="cost" name="Coût" stroke="#ef4444" isAnimationActive={false} />
      </ComposedChart>
    </ResponsiveContainer>
  );
}
