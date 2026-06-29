import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";

import { getConfig, getProject } from "../api/client";
import KpiCard from "../components/KpiCard";
import { SkeletonCards } from "../components/Skeleton";
import { costBreakdownTitle, formatCost, formatDuration, formatModel, formatProjectName, formatTokens } from "../lib/format";

export default function ProjectDetail() {
  const { name = "" } = useParams();
  const { data, isLoading, error } = useQuery({
    queryKey: ["project", name],
    queryFn: () => getProject(name),
  });
  const { data: configData } = useQuery({ queryKey: ["config"], queryFn: getConfig });
  const currency = configData?.currency ?? "€";
  if (isLoading) return (<div><SkeletonCards /></div>);
  if (error || !data) return <p>Projet introuvable.</p>;
  const p = data.project;
  return (
    <div>
      <p><Link to="/projects">← Projets</Link></p>
      <h2 title={p.path}>{formatProjectName(p.name)}</h2>
      <div style={{ display: "flex", gap: 14, flexWrap: "wrap" }}>
        <KpiCard label="Sessions" value={String(p.session_count)} index={0} />
        <KpiCard label="Tokens" value={formatTokens(p.usage.input + p.usage.output)} index={1} />
        <KpiCard label="Coût" value={formatCost(p.cost, currency, p.cost_known)} accent index={2} />
      </div>
      <h3>Sessions</h3>
      <table className="data-table">
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
                {s.is_active && (
                  <span style={{ color: "var(--green)", marginLeft: 8, fontSize: "0.8em", whiteSpace: "nowrap" }}>
                    <span className="live-dot" /> live
                  </span>
                )}
              </td>
              <td>{formatModel(s.models[0] ?? "—")}</td>
              <td>{formatDuration(s.duration_seconds)}</td>
              <td>{formatTokens(s.usage.input + s.usage.output)}</td>
              <td title={costBreakdownTitle(s.cost_breakdown, currency)} style={{ cursor: s.cost_known ? "help" : undefined }}>
                {formatCost(s.cost, currency, s.cost_known)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
