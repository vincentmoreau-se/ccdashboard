// Single source of truth for visual design tokens.
// Mirrored as CSS custom properties in index.css; consumed directly here by
// inline styles and by Recharts (which needs JS values for stroke/tick/contentStyle).

export const theme = {
  colors: {
    // Surfaces — warm deep slate, not pure black.
    bg: "#16140f",
    bgElevated: "#1c1a15",
    surface: "#211e19",
    surfaceHover: "#28241d",
    border: "rgba(255, 255, 255, 0.07)",
    borderStrong: "rgba(255, 255, 255, 0.12)",
    // Text — warm cream.
    text: "#ece6dc",
    textMuted: "#a8a094",
    textFaint: "#6f6a60",
    // Brand accents.
    accent: "#d97757", // Claude coral — primary
    accentSoft: "rgba(217, 119, 87, 0.14)",
    amber: "#e0a34e", // secondary — cost line / warnings
    amberSoft: "rgba(224, 163, 78, 0.14)",
    green: "#7bb369", // live / success
  },
  // Categorical palette for multi-series charts (donuts, stacked bars), warm-toned
  // to stay on-brand with the coral identity. Ordered for good adjacent contrast.
  chart: [
    "#d97757", // coral
    "#e0a34e", // amber
    "#7bb369", // green
    "#c98a9b", // dusty rose
    "#9a8cc4", // muted violet
    "#6fa8b8", // teal
    "#cbb994", // sand
    "#b56b57", // brick
  ],
  font: {
    display: '"Fraunces", Georgia, serif',
    body: '"Hanken Grotesk", system-ui, sans-serif',
    mono: '"JetBrains Mono", ui-monospace, "SFMono-Regular", monospace',
  },
  radius: { sm: 8, md: 12, lg: 16, pill: 999 },
  space: (n: number) => n * 4,
  shadow: {
    card: "0 1px 2px rgba(0,0,0,0.3), 0 8px 24px -12px rgba(0,0,0,0.5)",
    glow: "0 0 0 1px rgba(217,119,87,0.18), 0 8px 28px -14px rgba(217,119,87,0.35)",
  },
} as const;
