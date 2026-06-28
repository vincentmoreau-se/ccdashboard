import { theme } from "../theme";

/** A thin horizontal magnitude bar (share of a max), for inline table cells. */
export default function Sparkbar({
  fraction,
  color = theme.colors.accent,
  width = 90,
}: {
  fraction: number;
  color?: string;
  width?: number;
}) {
  const pct = Math.max(0, Math.min(1, isFinite(fraction) ? fraction : 0)) * 100;
  return (
    <span
      aria-hidden
      style={{
        display: "inline-block",
        width,
        height: 6,
        borderRadius: theme.radius.pill,
        background: "rgba(255,255,255,0.06)",
        overflow: "hidden",
        verticalAlign: "middle",
      }}
    >
      <span
        style={{
          display: "block",
          width: `${pct}%`,
          height: "100%",
          borderRadius: theme.radius.pill,
          background: color,
        }}
      />
    </span>
  );
}
