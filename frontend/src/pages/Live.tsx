import { useEffect, useState } from "react";

import type { SessionSummary } from "../api/client";
import { subscribeLive } from "../api/sse";
import { formatDuration, formatTokens } from "../lib/format";

export default function Live() {
  const [active, setActive] = useState<SessionSummary[]>([]);
  const [updated, setUpdated] = useState<string>("");

  useEffect(() => {
    const unsub = subscribeLive((snap) => {
      setActive(snap.active);
      setUpdated(snap.generated_at);
    });
    return unsub;
  }, []);

  return (
    <div>
      <h2>Sessions actives <span style={{ color: "#16a34a" }}>●</span></h2>
      <p style={{ color: "#666" }}>Dernière mise à jour : {updated.slice(11, 19) || "…"}</p>
      {active.length === 0 ? (
        <p>Aucune session active.</p>
      ) : (
        <ul>
          {active.map((s) => {
            const tool = Object.keys(s.tool_counts).slice(-1)[0] ?? "—";
            return (
              <li key={s.session_id} style={{ marginBottom: 8 }}>
                <strong>{s.ai_title ?? s.session_id}</strong> — {s.project}
                <br />
                {s.models[0] ?? "—"} · {formatTokens(s.usage.input + s.usage.output)} tok ·
                dernier outil : {tool} · {formatDuration(s.duration_seconds)} · {s.message_count} messages
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
