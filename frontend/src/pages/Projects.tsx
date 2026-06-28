import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { getConfig, getProjects } from "../api/client";
import { SkeletonCards } from "../components/Skeleton";
import Sparkbar from "../components/Sparkbar";
import UnknownCostBadge from "../components/UnknownCostBadge";
import { formatCost, formatProjectName, formatTokens } from "../lib/format";
import { theme } from "../theme";

export default function Projects() {
  const { data, isLoading, error } = useQuery({ queryKey: ["projects"], queryFn: getProjects });
  const { data: configData } = useQuery({ queryKey: ["config"], queryFn: getConfig });
  const currency = configData?.currency ?? "€";
  if (isLoading) return (<div><h2>Projets</h2><SkeletonCards count={1} /></div>);
  if (error || !data) return <p>Erreur de chargement.</p>;
  const maxCost = Math.max(1, ...data.map((p) => p.cost));
  return (
    <div>
      <h2>Projets</h2>
      <table className="data-table">
        <thead>
          <tr><th align="left">Projet</th><th>Sessions</th><th>Tokens</th><th>Coût</th><th>Part</th><th>Dernière activité</th></tr>
        </thead>
        <tbody>
          {data.map((p) => (
            <tr key={p.name}>
              <td>
                <Link to={`/projects/${encodeURIComponent(p.name)}`} title={p.path}>
                  {formatProjectName(p.name)}
                </Link>{" "}
                <UnknownCostBadge known={p.cost_known} />
              </td>
              <td>{p.session_count}</td>
              <td>{formatTokens(p.usage.input + p.usage.output)}</td>
              <td>{formatCost(p.cost, currency, p.cost_known)}</td>
              <td><Sparkbar fraction={p.cost / maxCost} color={theme.colors.accent} /></td>
              <td>{p.last_activity?.slice(0, 10) ?? "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
