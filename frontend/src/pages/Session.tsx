import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";

import { getConfig, getSession } from "../api/client";
import {
  formatCost, formatDuration, formatModel, formatProjectName, formatTokens,
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
  const meta: [string, string][] = [
    ["Projet", formatProjectName(s.project)],
    ["Modèle(s)", `${s.models.map(formatModel).join(", ") || "—"} (${s.provider})`],
    ["Branche", `${s.git_branch ?? "—"} · CC ${s.cc_version ?? "—"}`],
    ["Durée", `${formatDuration(s.duration_seconds)} · ${s.message_count} messages`],
    ["Tokens", formatTokens(s.usage.input + s.usage.output)],
    ["Coût", formatCost(s.cost, currency, s.cost_known)],
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
        {meta.map(([k, v]) => (
          <div key={k} style={{ background: theme.colors.surface, padding: "12px 16px" }}>
            <div style={{ color: theme.colors.textFaint, fontSize: 11, letterSpacing: "0.05em", textTransform: "uppercase" }}>{k}</div>
            <div style={{ marginTop: 3, fontFamily: theme.font.mono, fontSize: 13.5, color: theme.colors.text }}>{v}</div>
          </div>
        ))}
      </div>

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
                  <span style={{ fontFamily: theme.font.mono, fontSize: 12, color: theme.colors.amber }}>
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
