import { useState, type ReactNode } from "react";

import { theme } from "../theme";

export default function KpiCard({
  label,
  value,
  sub,
  accent = false,
  index = 0,
}: {
  label: string;
  value: ReactNode;
  sub?: ReactNode;
  accent?: boolean;
  index?: number;
}) {
  const [hover, setHover] = useState(false);
  return (
    <div
      className="reveal hud-frame"
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      style={{
        position: "relative",
        flex: "1 1 180px",
        minWidth: 170,
        padding: "18px 20px",
        borderRadius: theme.radius.md,
        background: theme.colors.surface,
        border: `1px solid ${hover ? theme.colors.borderStrong : theme.colors.borderStrong}`,
        boxShadow: hover ? theme.shadow.glow : theme.shadow.card,
        transform: hover ? "translateY(-3px)" : "none",
        transition: "transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease",
        animationDelay: `${index * 70}ms`,
        overflow: "hidden",
      }}
    >
      {/* Top accent hairline */}
      <span
        aria-hidden
        style={{
          position: "absolute",
          inset: "0 0 auto 0",
          height: 2,
          background: accent
            ? `linear-gradient(90deg, ${theme.colors.accent}, ${theme.colors.amber})`
            : "transparent",
          opacity: hover || accent ? 0.9 : 0,
          transition: "opacity 0.2s ease",
        }}
      />
      <div
        style={{
          fontFamily: theme.font.display,
          color: theme.colors.textMuted,
          fontSize: 11,
          fontWeight: 600,
          letterSpacing: "0.18em",
          textTransform: "uppercase",
        }}
      >
        {label}
      </div>
      <div
        style={{
          marginTop: 8,
          fontFamily: theme.font.mono,
          fontSize: 28,
          fontWeight: 500,
          letterSpacing: "-0.02em",
          color: accent ? theme.colors.accent : theme.colors.text,
          fontVariantNumeric: "tabular-nums",
        }}
      >
        {value}
      </div>
      {sub != null && (
        <div style={{ marginTop: 4, fontSize: 12, color: theme.colors.textMuted }}>{sub}</div>
      )}
    </div>
  );
}
