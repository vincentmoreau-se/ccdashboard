import type { TimeBucket } from "../api/client";
import { formatCost } from "../lib/format";
import { theme } from "../theme";

/** GitHub-style daily activity grid, coloured by cost intensity. */
export default function ActivityCalendar({
  data,
  currency,
}: {
  data: TimeBucket[];
  currency: string;
}) {
  if (data.length === 0) return <p>Pas encore d'activité.</p>;

  const byDate = new Map(data.map((b) => [b.date, b]));
  const maxCost = Math.max(...data.map((b) => b.cost), 0.0001);

  const dates = data.map((b) => b.date).sort();
  const start = new Date(dates[0] + "T00:00:00");
  const end = new Date(dates[dates.length - 1] + "T00:00:00");
  // Pad to the start of the week (Monday-based).
  const startDow = (start.getDay() + 6) % 7;
  const cells: ({ date: string; bucket?: TimeBucket } | null)[] = [];
  for (let i = 0; i < startDow; i++) cells.push(null);
  for (let d = new Date(start); d <= end; d.setDate(d.getDate() + 1)) {
    const iso = d.toISOString().slice(0, 10);
    cells.push({ date: iso, bucket: byDate.get(iso) });
  }

  const intensity = (cost: number): string => {
    if (cost <= 0) return "rgba(255,255,255,0.05)";
    const t = Math.min(1, 0.2 + (cost / maxCost) * 0.8);
    return `rgba(18, 171, 219, ${t.toFixed(2)})`;
  };

  return (
    <div style={{ display: "flex", gap: 14, alignItems: "flex-start", flexWrap: "wrap" }}>
      <div
        style={{
          display: "grid",
          gridTemplateRows: "repeat(7, 14px)",
          gridAutoFlow: "column",
          gridAutoColumns: "14px",
          gap: 4,
        }}
      >
        {cells.map((c, i) =>
          c === null ? (
            <span key={`pad-${i}`} />
          ) : (
            <span
              key={c.date}
              title={
                c.bucket
                  ? `${c.date} · ${formatCost(c.bucket.cost, currency, true)} · ${c.bucket.session_count} session(s)`
                  : `${c.date} · —`
              }
              style={{
                width: 14,
                height: 14,
                borderRadius: 3,
                background: intensity(c.bucket?.cost ?? 0),
              }}
            />
          ),
        )}
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 11, color: theme.colors.textFaint }}>
        <span>moins</span>
        {[0.05, 0.35, 0.6, 0.85, 1].map((t) => (
          <span
            key={t}
            style={{ width: 12, height: 12, borderRadius: 3, background: `rgba(18, 171, 219, ${t})` }}
          />
        ))}
        <span>plus</span>
      </div>
    </div>
  );
}
