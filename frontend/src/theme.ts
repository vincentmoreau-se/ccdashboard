// Single source of truth for visual design tokens.
// Re-themed to the "flight-deck HUD" / Capgemini palette to mirror the central
// server dashboard. Keys are unchanged so existing inline-styled components and
// Recharts props pick up the new look automatically; values now map to the
// Tailwind tokens in tailwind.config.js + the CSS vars in index.css.

export const theme = {
  colors: {
    // Surfaces — deep navy flight-deck.
    bg: "#04070d", // void
    bgElevated: "#0a1018", // panel
    surface: "#0a1018", // panel
    surfaceHover: "#0f1722", // panel-2
    border: "#1c2a3a",
    borderStrong: "#233246", // edge
    // Text.
    text: "#e6edf3", // bone
    textMuted: "#8595a8", // ash
    textFaint: "#5b6878", // haze
    // Brand accents.
    accent: "#12ABDB", // Capgemini Gamma Blue — primary
    accentSoft: "rgba(18, 171, 219, 0.14)",
    amber: "#0070AD", // Capgemini Honolulu Blue — secondary
    amberSoft: "rgba(0, 112, 173, 0.16)",
    green: "#9be34a", // live / success
  },
  // Categorical palette for multi-series charts — Capgemini extended vibrant blues.
  chart: [
    "#12ABDB", // brand
    "#0070AD", // deep
    "#00BFB3", // peacock
    "#7B61FF", // violet
    "#4FC3F7", // sky
    "#1D4F91", // sapphire
    "#9be34a", // live
    "#ff5d62", // alert
  ],
  font: {
    display: '"Chakra Petch", sans-serif',
    body: '"IBM Plex Mono", monospace',
    mono: '"IBM Plex Mono", ui-monospace, "SFMono-Regular", monospace',
  },
  // Sharp HUD corners.
  radius: { sm: 2, md: 3, lg: 4, pill: 999 },
  space: (n: number) => n * 4,
  shadow: {
    card: "inset 0 1px 0 0 rgba(255,255,255,0.03), 0 8px 30px -12px rgba(0,0,0,0.8)",
    glow: "0 0 0 1px rgba(18,171,219,0.25), 0 0 24px -6px rgba(18,171,219,0.45)",
  },
} as const;
