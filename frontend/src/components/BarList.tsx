import { theme } from "../theme";

export interface BarItem {
  label: string;
  value: number;
}

/** Ranked horizontal bars (value relative to the max). */
export default function BarList({
  items,
  color = theme.colors.accent,
  format = (n) => String(n),
  max,
}: {
  items: BarItem[];
  color?: string;
  format?: (n: number) => string;
  max?: number;
}) {
  const top = Math.max(1, max ?? Math.max(...items.map((i) => i.value), 1));
  return (
    <div style={{ display: "grid", gap: 9 }}>
      {items.map((it) => (
        <div key={it.label} style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <span
            style={{
              width: 120,
              flexShrink: 0,
              fontSize: 13,
              color: theme.colors.textMuted,
              fontFamily: theme.font.mono,
              overflow: "hidden",
              textOverflow: "ellipsis",
              whiteSpace: "nowrap",
            }}
            title={it.label}
          >
            {it.label}
          </span>
          <span
            style={{
              flex: 1,
              height: 18,
              background: "rgba(255,255,255,0.04)",
              borderRadius: theme.radius.sm,
              overflow: "hidden",
            }}
          >
            <span
              style={{
                display: "block",
                width: `${(it.value / top) * 100}%`,
                height: "100%",
                background: `linear-gradient(90deg, ${color}, ${color}aa)`,
                borderRadius: theme.radius.sm,
                minWidth: 2,
              }}
            />
          </span>
          <span style={{ width: 56, textAlign: "right", fontFamily: theme.font.mono, fontSize: 13, color: theme.colors.text }}>
            {format(it.value)}
          </span>
        </div>
      ))}
    </div>
  );
}
