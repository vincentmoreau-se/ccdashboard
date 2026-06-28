import { useQuery } from "@tanstack/react-query";
import { useParams } from "react-router-dom";

import { getSession } from "../api/client";
import { formatCost, formatDuration, formatTokens } from "../lib/format";

export default function Session() {
  const { id = "" } = useParams();
  const { data, isLoading, error } = useQuery({
    queryKey: ["session", id],
    queryFn: () => getSession(id),
  });
  if (isLoading) return <p>Chargement…</p>;
  if (error || !data) return <p>Session introuvable.</p>;
  const s = data.summary;
  return (
    <div>
      <h2>{s.ai_title ?? s.session_id}</h2>
      <ul>
        <li>Projet : {s.project}</li>
        <li>Modèle(s) : {s.models.join(", ") || "—"} ({s.provider})</li>
        <li>Branche : {s.git_branch ?? "—"} · CC {s.cc_version ?? "—"}</li>
        <li>Durée : {formatDuration(s.duration_seconds)} · Messages : {s.message_count}</li>
        <li>Tokens : {formatTokens(s.usage.input + s.usage.output)} · Coût : {formatCost(s.cost, "€", s.cost_known)}</li>
      </ul>
      <h3>Timeline</h3>
      <ol>
        {data.messages.map((m, i) => (
          <li key={m.uuid ?? i} style={{ marginBottom: 6 }}>
            <strong>{m.type}</strong>{" "}
            <span style={{ color: "#666" }}>{m.timestamp?.slice(11, 19) ?? ""}</span>
            {m.tools.length > 0 && <span> · 🔧 {m.tools.join(", ")}</span>}
            {m.content_kinds.length > 0 && <span> · {m.content_kinds.join("/")}</span>}
            {(m.usage.input + m.usage.output) > 0 && (
              <span> · {formatTokens(m.usage.input + m.usage.output)} tok</span>
            )}
          </li>
        ))}
      </ol>
    </div>
  );
}
