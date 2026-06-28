import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";

import { getProject } from "../api/client";
import KpiCard from "../components/KpiCard";
import { formatCost, formatDuration, formatTokens } from "../lib/format";

export default function ProjectDetail() {
  const { name = "" } = useParams();
  const { data, isLoading, error } = useQuery({
    queryKey: ["project", name],
    queryFn: () => getProject(name),
  });
  if (isLoading) return <p>Chargement…</p>;
  if (error || !data) return <p>Projet introuvable.</p>;
  const p = data.project;
  return (
    <div>
      <p><Link to="/projects">← Projets</Link></p>
      <h2>{p.name}</h2>
      <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
        <KpiCard label="Sessions" value={String(p.session_count)} />
        <KpiCard label="Tokens" value={formatTokens(p.usage.input + p.usage.output)} />
        <KpiCard label="Coût" value={formatCost(p.cost, "€", p.cost_known)} />
      </div>
      <h3>Sessions</h3>
      <table style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead>
          <tr><th align="left">Titre / ID</th><th>Modèle</th><th>Durée</th><th>Tokens</th><th>Coût</th></tr>
        </thead>
        <tbody>
          {data.sessions.map((s) => (
            <tr key={s.session_id}>
              <td>
                <Link to={`/sessions/${encodeURIComponent(s.session_id)}`}>
                  {s.ai_title ?? s.session_id}
                </Link>
                {s.is_active && <span style={{ color: "#16a34a" }}> ● live</span>}
              </td>
              <td align="center">{s.models[0] ?? "—"}</td>
              <td align="center">{formatDuration(s.duration_seconds)}</td>
              <td align="center">{formatTokens(s.usage.input + s.usage.output)}</td>
              <td align="center">{formatCost(s.cost, "€", s.cost_known)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
