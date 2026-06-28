export default function UnknownCostBadge({ known }: { known: boolean }) {
  if (known) return null;
  return (
    <span
      title="Un modèle sans tarif a été rencontré"
      style={{ background: "#fde68a", color: "#92400e", borderRadius: 6, padding: "2px 8px", fontSize: 12 }}
    >
      coût incomplet
    </span>
  );
}
