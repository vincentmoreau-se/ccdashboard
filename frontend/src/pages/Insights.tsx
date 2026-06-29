import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { getConfig, getOverview } from "../api/client";
import ActivityCalendar from "../components/ActivityCalendar";
import BarList from "../components/BarList";
import Donut from "../components/Donut";
import Panel from "../components/Panel";
import { SkeletonCards } from "../components/Skeleton";
import { costBreakdownTitle, formatCost, formatCount, formatProjectName, formatTokens } from "../lib/format";
import { theme } from "../theme";

const KIND_LABELS: Record<string, string> = {
  thinking: "🧠 Réflexion",
  text: "💬 Texte",
  tool_use: "🔧 Appel d'outil",
  tool_result: "✅ Résultat outil",
  document: "📄 Document",
  image: "🖼 Image",
};

export default function Insights() {
  const { data, isLoading, error } = useQuery({ queryKey: ["overview"], queryFn: getOverview });
  const { data: configData } = useQuery({ queryKey: ["config"], queryFn: getConfig });
  const currency = configData?.currency ?? "€";
  if (isLoading) {
    return (
      <div>
        <h2 style={{ marginTop: "1.4rem" }}>Insights</h2>
        <SkeletonCards count={2} />
      </div>
    );
  }
  if (error || !data) return <p>Erreur de chargement.</p>;

  const tools = Object.entries(data.tool_counts)
    .map(([label, value]) => ({ label, value }))
    .sort((a, b) => b.value - a.value)
    .slice(0, 12);

  const kinds = Object.entries(data.content_kind_counts)
    .map(([k, value]) => ({ name: KIND_LABELS[k] ?? k, value }))
    .sort((a, b) => b.value - a.value);

  const webSearch = data.total_usage.web_search;
  const webFetch = data.total_usage.web_fetch;

  return (
    <div style={{ display: "grid", gap: 22 }}>
      <h2 style={{ marginTop: "1.4rem", marginBottom: 0 }}>Insights</h2>

      <Panel title="Outils les plus utilisés" right={`${Object.keys(data.tool_counts).length} outils distincts`}>
        {tools.length > 0 ? (
          <BarList items={tools} format={formatCount} color={theme.colors.accent} />
        ) : (
          <p>Aucun appel d'outil enregistré.</p>
        )}
      </Panel>

      <Panel title="Types de message" right="ce que fait Claude, tour par tour">
        {kinds.length > 0 ? (
          <Donut data={kinds} height={200} formatValue={formatCount} />
        ) : (
          <p>Aucune donnée.</p>
        )}
      </Panel>

      <Panel title="Activité quotidienne" right="intensité = coût du jour">
        <ActivityCalendar data={data.timeseries} currency={currency} />
      </Panel>

      {(webSearch > 0 || webFetch > 0) && (
        <Panel title="Outils web">
          <div style={{ display: "flex", gap: 28, fontFamily: theme.font.mono }}>
            <div>
              <div style={{ fontSize: 24, color: theme.colors.text }}>{formatCount(webSearch)}</div>
              <div style={{ fontSize: 12, color: theme.colors.textMuted }}>🔍 web_search</div>
            </div>
            <div>
              <div style={{ fontSize: 24, color: theme.colors.text }}>{formatCount(webFetch)}</div>
              <div style={{ fontSize: 12, color: theme.colors.textMuted }}>🌐 web_fetch</div>
            </div>
          </div>
        </Panel>
      )}

      <div>
        <h2>Sessions les plus chères</h2>
        <table className="data-table">
          <thead>
            <tr><th align="left">Session</th><th align="left">Projet</th><th>Tokens</th><th>Coût</th></tr>
          </thead>
          <tbody>
            {data.top_sessions.map((s) => (
              <tr key={s.session_id}>
                <td>
                  <Link to={`/sessions/${encodeURIComponent(s.session_id)}`}>
                    {s.ai_title ?? s.session_id.slice(0, 12)}
                  </Link>
                </td>
                <td style={{ color: theme.colors.textMuted, textAlign: "left", fontFamily: theme.font.body }} title={s.project}>{formatProjectName(s.project)}</td>
                <td>{formatTokens(s.usage.input + s.usage.output)}</td>
                <td title={costBreakdownTitle(s.cost_breakdown, currency)} style={{ cursor: s.cost_known ? "help" : undefined }}>
                  {formatCost(s.cost, currency, s.cost_known)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
