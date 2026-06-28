import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { getConfig, getOverview } from "../api/client";
import CacheSavingsCard from "../components/CacheSavingsCard";
import CostTokenChart from "../components/CostTokenChart";
import CountUp from "../components/CountUp";
import Donut from "../components/Donut";
import KpiCard from "../components/KpiCard";
import Panel from "../components/Panel";
import { SkeletonCards } from "../components/Skeleton";
import Sparkbar from "../components/Sparkbar";
import UnknownCostBadge from "../components/UnknownCostBadge";
import { formatCost, formatModel, formatProjectName, formatTokens } from "../lib/format";
import { theme } from "../theme";

export default function Overview() {
  const { data, isLoading, error } = useQuery({ queryKey: ["overview"], queryFn: getOverview });
  const { data: configData } = useQuery({ queryKey: ["config"], queryFn: getConfig });
  const currency = configData?.currency ?? "€";
  if (isLoading) {
    return (
      <div>
        <h2 style={{ marginTop: "1.4rem" }}>Vue d'ensemble</h2>
        <SkeletonCards />
      </div>
    );
  }
  if (error || !data) return <p>Erreur de chargement.</p>;

  const totalTokens = data.total_usage.input + data.total_usage.output;
  const effectiveRate = totalTokens > 0 ? (data.total_cost / totalTokens) * 1_000_000 : 0;
  const maxProjectCost = Math.max(1, ...data.by_project.map((p) => p.cost));
  const modelSlices = data.by_model
    .filter((m) => m.cost > 0)
    .map((m) => ({ name: formatModel(m.model), value: m.cost }));

  return (
    <div style={{ display: "grid", gap: 22 }}>
      <div>
        <h2 style={{ marginTop: "1.4rem" }}>Vue d'ensemble</h2>
        <div style={{ display: "flex", gap: 14, flexWrap: "wrap" }}>
          <KpiCard
            label="Sessions"
            value={<CountUp value={data.session_count} format={(n) => String(Math.round(n))} />}
            index={0}
          />
          <KpiCard
            label="Tokens (in+out)"
            value={<CountUp value={totalTokens} format={formatTokens} />}
            index={1}
          />
          <KpiCard
            label="Coût total"
            value={<CountUp value={data.total_cost} format={(n) => formatCost(n, currency, data.cost_known)} />}
            sub={`≈ ${formatCost(effectiveRate, currency, true)} / Mtok`}
            accent
            index={2}
          />
        </div>
        <div style={{ marginTop: 12 }}>
          <UnknownCostBadge known={data.cost_known} />
        </div>
      </div>

      <CacheSavingsCard usage={data.total_usage} savings={data.cache_savings} currency={currency} />

      {modelSlices.length > 0 && (
        <Panel title="Mix de modèles" right="par coût">
          <Donut
            data={modelSlices}
            height={200}
            centerValue={formatCost(data.total_cost, currency, data.cost_known)}
            centerLabel="coût"
            formatValue={(n) => formatCost(n, currency, true)}
          />
        </Panel>
      )}

      <Panel title="Activité & coût par jour">
        <CostTokenChart data={data.timeseries} />
      </Panel>

      <div>
        <h2>Top projets</h2>
        <table className="data-table">
          <thead>
            <tr><th align="left">Projet</th><th>Sessions</th><th>Tokens</th><th>Coût</th><th>Part</th></tr>
          </thead>
          <tbody>
            {data.by_project.map((p) => (
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
                <td><Sparkbar fraction={p.cost / maxProjectCost} color={theme.colors.accent} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
