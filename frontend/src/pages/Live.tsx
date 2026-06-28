import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import type { SessionSummary } from "../api/client";
import { getConfig } from "../api/client";
import { useQuery } from "@tanstack/react-query";
import { subscribeLive } from "../api/sse";
import CountUp from "../components/CountUp";
import Panel from "../components/Panel";
import { formatCost, formatDuration, formatModel, formatProjectName, formatTokens } from "../lib/format";
import { theme } from "../theme";

export default function Live() {
  const [active, setActive] = useState<SessionSummary[]>([]);
  const [updated, setUpdated] = useState<string>("");
  const { data: configData } = useQuery({ queryKey: ["config"], queryFn: getConfig });
  const currency = configData?.currency ?? "€";

  useEffect(() => {
    const unsub = subscribeLive((snap) => {
      setActive(snap.active);
      setUpdated(snap.generated_at);
    });
    return unsub;
  }, []);

  const totalCost = active.reduce((a, s) => a + s.cost, 0);
  const totalHours = active.reduce((a, s) => a + (s.duration_seconds ?? 0), 0) / 3600;
  const burnRate = totalHours > 0 ? totalCost / totalHours : 0;

  return (
    <div style={{ display: "grid", gap: 22 }}>
      <h2 style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 0 }}>
        Sessions actives <span className="live-dot" />
      </h2>

      <Panel
        style={{ borderLeft: `3px solid ${theme.colors.green}` }}
        right={`Dernière mise à jour : ${updated.slice(11, 19) || "…"}`}
      >
        <div style={{ display: "flex", gap: 40, flexWrap: "wrap", alignItems: "flex-end" }}>
          <div>
            <div style={{ fontSize: 12.5, color: theme.colors.textMuted, textTransform: "uppercase", letterSpacing: "0.05em" }}>
              Coût cumulé (sessions actives)
            </div>
            <div style={{ fontFamily: theme.font.mono, fontSize: 46, fontWeight: 600, lineHeight: 1.1, color: theme.colors.accent }}>
              <CountUp value={totalCost} format={(n) => formatCost(n, currency, true)} durationMs={1200} />
            </div>
          </div>
          <div>
            <div style={{ fontSize: 12.5, color: theme.colors.textMuted, textTransform: "uppercase", letterSpacing: "0.05em" }}>
              Rythme
            </div>
            <div style={{ fontFamily: theme.font.mono, fontSize: 22, color: theme.colors.text }}>
              <CountUp value={burnRate} format={(n) => `${formatCost(n, currency, true)}/h`} />
            </div>
            <div style={{ fontSize: 12, color: theme.colors.textFaint, fontFamily: theme.font.mono }}>
              ≈ {formatCost(burnRate * 24, currency, true)}/jour
            </div>
          </div>
          <div>
            <div style={{ fontSize: 12.5, color: theme.colors.textMuted, textTransform: "uppercase", letterSpacing: "0.05em" }}>
              Actives
            </div>
            <div style={{ fontFamily: theme.font.mono, fontSize: 22, color: theme.colors.text }}>
              {active.length}
            </div>
          </div>
        </div>
      </Panel>

      {active.length === 0 ? (
        <p>Aucune session active.</p>
      ) : (
        <div style={{ display: "grid", gap: 12 }}>
          {active.map((s) => {
            const tool = Object.keys(s.tool_counts).slice(-1)[0] ?? "—";
            return (
              <Link
                key={s.session_id}
                to={`/sessions/${encodeURIComponent(s.session_id)}`}
                className="reveal"
                style={{
                  display: "block",
                  padding: "14px 18px",
                  borderRadius: theme.radius.md,
                  background: theme.colors.surface,
                  border: `1px solid ${theme.colors.border}`,
                  borderLeft: `3px solid ${theme.colors.green}`,
                  boxShadow: theme.shadow.card,
                  color: "inherit",
                  textDecoration: "none",
                }}
              >
                <div style={{ display: "flex", alignItems: "baseline", gap: 8, flexWrap: "wrap" }}>
                  <strong style={{ fontFamily: theme.font.display, fontSize: 16, color: theme.colors.text }}>
                    {s.ai_title ?? s.session_id}
                  </strong>
                  <span style={{ color: theme.colors.textMuted, fontSize: 13 }}>— {formatProjectName(s.project)}</span>
                  <span style={{ flex: 1 }} />
                  <span style={{ fontFamily: theme.font.mono, fontSize: 14, color: theme.colors.accent }}>
                    {formatCost(s.cost, currency, s.cost_known)}
                  </span>
                </div>
                <div style={{ marginTop: 8, fontFamily: theme.font.mono, fontSize: 12.5, color: theme.colors.textMuted }}>
                  {formatModel(s.models[0] ?? "—")} · {formatTokens(s.usage.input + s.usage.output)} tok · dernier outil : {tool} ·{" "}
                  {formatDuration(s.duration_seconds)} · {s.message_count} messages
                </div>
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
}
