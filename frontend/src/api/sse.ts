import type { SessionSummary } from "./client";

const BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

export interface LiveSnapshot {
  active: SessionSummary[];
  generated_at: string;
}

export function subscribeLive(onSnapshot: (snap: LiveSnapshot) => void): () => void {
  let source: EventSource | null = null;
  let retry: ReturnType<typeof setTimeout> | null = null;
  let closed = false;

  const connect = () => {
    source = new EventSource(`${BASE}/api/live`);
    source.onmessage = (e) => onSnapshot(JSON.parse(e.data));
    source.onerror = () => {
      source?.close();
      if (!closed) retry = setTimeout(connect, 3000);
    };
  };
  connect();

  return () => {
    closed = true;
    source?.close();
    if (retry) clearTimeout(retry);
  };
}
