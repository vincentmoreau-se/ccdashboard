import { theme } from "../theme";

/** Shimmering placeholder block used while data loads. */
export default function Skeleton({
  width = "100%",
  height = 16,
  radius = theme.radius.sm,
  style,
}: {
  width?: number | string;
  height?: number | string;
  radius?: number;
  style?: React.CSSProperties;
}) {
  return (
    <span
      aria-hidden
      style={{
        display: "block",
        width,
        height,
        borderRadius: radius,
        background:
          "linear-gradient(90deg, rgba(255,255,255,0.04) 25%, rgba(255,255,255,0.09) 37%, rgba(255,255,255,0.04) 63%)",
        backgroundSize: "400% 100%",
        animation: "skeleton-shimmer 1.4s ease infinite",
        ...style,
      }}
    />
  );
}

export function SkeletonCards({ count = 3 }: { count?: number }) {
  return (
    <div style={{ display: "flex", gap: 14, flexWrap: "wrap" }}>
      {Array.from({ length: count }).map((_, i) => (
        <Skeleton key={i} width={180} height={92} radius={theme.radius.md} style={{ flex: "1 1 170px" }} />
      ))}
    </div>
  );
}
