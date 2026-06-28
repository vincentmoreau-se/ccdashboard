import type { ReactNode } from "react";

import { theme } from "../theme";

/** A titled surface card used to frame a dashboard section. */
export default function Panel({
  title,
  right,
  children,
  style,
}: {
  title?: ReactNode;
  right?: ReactNode;
  children: ReactNode;
  style?: React.CSSProperties;
}) {
  return (
    <section
      className="reveal"
      style={{
        background: theme.colors.surface,
        border: `1px solid ${theme.colors.border}`,
        borderRadius: theme.radius.md,
        padding: "18px 20px",
        boxShadow: theme.shadow.card,
        ...style,
      }}
    >
      {(title || right) && (
        <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between", marginBottom: 14, gap: 12 }}>
          {title && (
            <h3 style={{ margin: 0, fontSize: "1.05rem" }}>{title}</h3>
          )}
          {right && <div style={{ fontSize: 12, color: theme.colors.textMuted }}>{right}</div>}
        </div>
      )}
      {children}
    </section>
  );
}
