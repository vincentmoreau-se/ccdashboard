import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { getProjects } from "../api/client";
import UnknownCostBadge from "../components/UnknownCostBadge";
import { formatCost, formatTokens } from "../lib/format";

export default function Projects() {
  const { data, isLoading, error } = useQuery({ queryKey: ["projects"], queryFn: getProjects });
  if (isLoading) return <p>Chargement…</p>;
  if (error || !data) return <p>Erreur de chargement.</p>;
  return (
    <div>
      <h2>Projets</h2>
      <table style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead>
          <tr><th align="left">Projet</th><th>Sessions</th><th>Tokens</th><th>Coût</th><th>Dernière activité</th></tr>
        </thead>
        <tbody>
          {data.map((p) => (
            <tr key={p.name}>
              <td>
                <Link to={`/projects/${encodeURIComponent(p.name)}`}>{p.name}</Link>{" "}
                <UnknownCostBadge known={p.cost_known} />
              </td>
              <td align="center">{p.session_count}</td>
              <td align="center">{formatTokens(p.usage.input + p.usage.output)}</td>
              <td align="center">{formatCost(p.cost, "€", p.cost_known)}</td>
              <td align="center">{p.last_activity?.slice(0, 10) ?? "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
