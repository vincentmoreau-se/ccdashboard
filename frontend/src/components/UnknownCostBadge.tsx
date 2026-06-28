import { theme } from "../theme";

export default function UnknownCostBadge({ known }: { known: boolean }) {
  if (known) return null;
  return (
    <span
      title="Un modèle sans tarif a été rencontré"
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 5,
        background: theme.colors.amberSoft,
        color: theme.colors.amber,
        border: `1px solid ${theme.colors.amber}55`,
        borderRadius: theme.radius.pill,
        padding: "2px 10px",
        fontSize: 12,
        fontWeight: 500,
        whiteSpace: "nowrap",
        verticalAlign: "middle",
      }}
    >
      <span aria-hidden>⚠</span>
      coût incomplet
    </span>
  );
}
