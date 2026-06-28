import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { getOverview } from "../api/client";
import CostTokenChart from "../components/CostTokenChart";
import KpiCard from "../components/KpiCard";
import UnknownCostBadge from "../components/UnknownCostBadge";
import { formatCost, formatTokens } from "../lib/format";

const CURRENCY = "€";

export default function Overview() {
  const { data, isLoading, error } = useQuery({ queryKey: ["overview"], queryFn: getOverview });
  if (isLoading) return <p>Chargement…</p>;
  if (error || !data) return <p>Erreur de chargement.</p>;

  const totalTokens = data.total_usage.input + data.total_usage.output;
  return (
    <div>
      <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
        <KpiCard label="Sessions" value={String(data.session_count)} />
        <KpiCard label="Tokens (in+out)" value={formatTokens(totalTokens)} />
        <KpiCard label="Coût total" value={formatCost(data.total_cost, CURRENCY, data.cost_known)} />
      </div>
      <div style={{ margin: "8px 0" }}>
        <UnknownCostBadge known={data.cost_known} />
      </div>
      <h2>Activité & coût par jour</h2>
      <CostTokenChart data={data.timeseries} />
      <h2>Top projets</h2>
      <table style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead>
          <tr><th align="left">Projet</th><th>Sessions</th><th>Tokens</th><th>Coût</th></tr>
        </thead>
        <tbody>
          {data.by_project.map((p) => (
            <tr key={p.name}>
              <td><Link to={`/projects/${encodeURIComponent(p.name)}`}>{p.name}</Link></td>
              <td align="center">{p.session_count}</td>
              <td align="center">{formatTokens(p.usage.input + p.usage.output)}</td>
              <td align="center">{formatCost(p.cost, CURRENCY, p.cost_known)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
