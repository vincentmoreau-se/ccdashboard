import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";

import { getConfig, getSession } from "../api/client";
import BarList from "../components/BarList";
import Donut from "../components/Donut";
import Panel from "../components/Panel";
import {
  costBreakdownTitle, formatCost, formatCount, formatDuration, formatModel, formatProjectName, formatTokens, mapToBarItems,
} from "../lib/format";
import { theme } from "../theme";

const KIND_ICON: Record<string, string> = {
  thinking: "🧠",
  text: "💬",
  tool_use: "🔧",
  tool_result: "✅",
  document: "📄",
  image: "🖼",
};

function dotColor(kinds: string[], type: string): string {
  if (kinds.includes("tool_use")) return theme.colors.accent;
  if (kinds.includes("thinking")) return theme.colors.amber;
  if (type === "assistant") return theme.colors.green;
  return theme.colors.textFaint;
}

export default function Session() {
  const { id = "" } = useParams();
  const { data, isLoading, error } = useQuery({
    queryKey: ["session", id],
    queryFn: () => getSession(id),
  });
  const { data: configData } = useQuery({ queryKey: ["config"], queryFn: getConfig });
  const currency = configData?.currency ?? "€";
  if (isLoading) return <p>Chargement…</p>;
  if (error || !data) return <p>Session introuvable.</p>;
  const s = data.summary;
  const meta: [string, string, string?][] = [
    ["Projet", formatProjectName(s.project)],
    ["Modèle(s)", `${s.models.map(formatModel).join(", ") || "—"} (${s.provider})`],
    ["Branche", `${s.git_branch ?? "—"} · CC ${s.cc_version ?? "—"}`],
    ["Durée", `${formatDuration(s.duration_seconds)} · ${s.message_count} messages`],
    ["Tokens", formatTokens(s.usage.input + s.usage.output)],
    ["Coût", formatCost(s.cost, currency, s.cost_known), costBreakdownTitle(s.cost_breakdown, currency)],
    ["Cache économisé", formatCost(s.cache_savings, currency, true)],
  ];
  return (
    <div>
      <p><Link to="/projects">← Projets</Link></p>
      <h2>{s.ai_title ?? s.session_id}</h2>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
          gap: 1,
          background: theme.colors.border,
          border: `1px solid ${theme.colors.border}`,
          borderRadius: theme.radius.md,
          overflow: "hidden",
        }}
      >
        {meta.map(([k, v, t]) => (
          <div key={k} style={{ background: theme.colors.surface, padding: "12px 16px" }}>
            <div style={{ color: theme.colors.textFaint, fontSize: 11, letterSpacing: "0.05em", textTransform: "uppercase" }}>{k}</div>
            <div title={t} style={{ marginTop: 3, fontFamily: theme.font.mono, fontSize: 13.5, color: theme.colors.text, cursor: t ? "help" : undefined }}>{v}</div>
          </div>
        ))}
      </div>

      {/* Tech & Tooling panels */}
      {(Object.keys(s.language_counts ?? {}).length > 0 ||
        Object.keys(s.framework_counts ?? {}).length > 0 ||
        Object.keys(s.builtin_tool_counts ?? {}).length > 0 ||
        Object.keys(s.user_tool_counts ?? {}).length > 0 ||
        Object.keys(s.skill_counts ?? {}).length > 0 ||
        Object.keys(s.mcp_server_counts ?? {}).length > 0 ||
        Object.keys(s.subagent_counts ?? {}).length > 0 ||
        Object.keys(s.slash_command_counts ?? {}).length > 0) && (
        <div style={{ display: "grid", gap: 16, marginTop: 24 }}>
          <h3 style={{ marginBottom: 0 }}>Tech & Tooling</h3>

          {Object.keys(s.language_counts ?? {}).length > 0 && (
            <Panel title="Langages">
              <Donut
                data={mapToBarItems(s.language_counts).map((it) => ({
                  name: it.label,
                  value: it.value,
                }))}
                height={180}
                formatValue={formatCount}
              />
            </Panel>
          )}

          {Object.keys(s.framework_counts ?? {}).length > 0 && (
            <Panel title="Frameworks">
              <BarList
                items={mapToBarItems(s.framework_counts)}
                format={formatCount}
                color={theme.colors.amber}
              />
            </Panel>
          )}

          {(Object.keys(s.builtin_tool_counts ?? {}).length > 0 ||
            Object.keys(s.user_tool_counts ?? {}).length > 0) && (
            <Panel title="Outils Claude Code">
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
                  gap: 20,
                }}
              >
                {Object.keys(s.builtin_tool_counts ?? {}).length > 0 && (
                  <div>
                    <div
                      style={{
                        fontSize: 12,
                        fontWeight: 600,
                        color: theme.colors.textMuted,
                        textTransform: "uppercase",
                        letterSpacing: "0.05em",
                        marginBottom: 10,
                      }}
                    >
                      Outils intégrés
                    </div>
                    <BarList
                      items={mapToBarItems(s.builtin_tool_counts)}
                      format={formatCount}
                      color={theme.colors.accent}
                    />
                  </div>
                )}
                {Object.keys(s.user_tool_counts ?? {}).length > 0 && (
                  <div>
                    <div
                      style={{
                        fontSize: 12,
                        fontWeight: 600,
                        color: theme.colors.textMuted,
                        textTransform: "uppercase",
                        letterSpacing: "0.05em",
                        marginBottom: 10,
                      }}
                    >
                      Outils utilisateur
                    </div>
                    <BarList
                      items={mapToBarItems(s.user_tool_counts)}
                      format={formatCount}
                      color={theme.colors.green}
                    />
                  </div>
                )}
              </div>
            </Panel>
          )}

          {Object.keys(s.skill_counts ?? {}).length > 0 && (
            <Panel title="Skills">
              <BarList
                items={mapToBarItems(s.skill_counts)}
                format={formatCount}
                color={theme.colors.accent}
              />
            </Panel>
          )}

          {Object.keys(s.mcp_server_counts ?? {}).length > 0 && (
            <Panel title="Serveurs MCP">
              <BarList
                items={mapToBarItems(s.mcp_server_counts)}
                format={formatCount}
                color={theme.chart[5]}
              />
            </Panel>
          )}

          {Object.keys(s.subagent_counts ?? {}).length > 0 && (
            <Panel title="Sous-agents">
              <BarList
                items={mapToBarItems(s.subagent_counts)}
                format={formatCount}
                color={theme.chart[4]}
              />
            </Panel>
          )}

          {Object.keys(s.slash_command_counts ?? {}).length > 0 && (
            <Panel title="Slash commands">
              <BarList
                items={mapToBarItems(s.slash_command_counts)}
                format={formatCount}
                color={theme.chart[3]}
              />
            </Panel>
          )}
        </div>
      )}

      <h3>Timeline</h3>
      <p style={{ marginTop: -4, fontSize: 13 }}>
        La boucle agentique, tour par tour : 🧠 réflexion · 💬 texte · 🔧 appel d'outil · ✅ résultat.
      </p>
      <ol
        style={{
          listStyle: "none",
          margin: 0,
          padding: 0,
          position: "relative",
          borderLeft: `2px solid ${theme.colors.border}`,
        }}
      >
        {data.messages.map((m, i) => {
          const tok = m.usage.input + m.usage.output;
          const color = dotColor(m.content_kinds, m.type);
          return (
            <li key={m.uuid ?? i} style={{ position: "relative", padding: "0 0 16px 22px" }}>
              <span
                aria-hidden
                style={{
                  position: "absolute",
                  left: -7,
                  top: 5,
                  width: 10,
                  height: 10,
                  borderRadius: "50%",
                  background: color,
                  border: `2px solid ${color}`,
                  boxShadow: `0 0 8px ${color}66`,
                }}
              />
              <div style={{ display: "flex", alignItems: "baseline", gap: 8, flexWrap: "wrap" }}>
                <strong style={{ fontFamily: theme.font.body, fontSize: 14, color: theme.colors.text }}>
                  {m.type}
                </strong>
                <span style={{ fontFamily: theme.font.mono, fontSize: 12, color: theme.colors.textFaint }}>
                  {m.timestamp?.slice(11, 19) ?? ""}
                </span>
                {m.content_kinds.map((k) => (
                  <span key={k} title={k} style={{ fontSize: 13 }}>
                    {KIND_ICON[k] ?? k}
                  </span>
                ))}
                {m.tools.map((t) => (
                  <span
                    key={t}
                    style={{
                      fontFamily: theme.font.mono,
                      fontSize: 11,
                      padding: "1px 7px",
                      borderRadius: theme.radius.pill,
                      background: theme.colors.accentSoft,
                      color: theme.colors.accent,
                    }}
                  >
                    {t}
                  </span>
                ))}
                <span style={{ flex: 1 }} />
                {tok > 0 && (
                  <span style={{ fontFamily: theme.font.mono, fontSize: 12, color: theme.colors.textMuted }}>
                    {formatTokens(tok)} tok
                  </span>
                )}
                {m.cost > 0 && (
                  <span title={costBreakdownTitle(m.cost_breakdown, currency)} style={{ fontFamily: theme.font.mono, fontSize: 12, color: theme.colors.amber, cursor: "help" }}>
                    {formatCost(m.cost, currency, m.cost_known)}
                  </span>
                )}
              </div>
            </li>
          );
        })}
      </ol>
    </div>
  );
}
