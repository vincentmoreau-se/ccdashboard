const BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

export interface Usage {
  input: number; output: number;
  cache_write_5m: number; cache_write_1h: number; cache_read: number;
  web_search: number; web_fetch: number;
}
export interface SessionSummary {
  session_id: string; project: string; cwd: string | null; file_path: string;
  ai_title: string | null; started_at: string | null; ended_at: string | null;
  duration_seconds: number | null; is_active: boolean; models: string[];
  provider: string; git_branch: string | null; cc_version: string | null;
  message_count: number; usage: Usage; cost: number; cost_known: boolean;
  tool_counts: Record<string, number>; skipped_lines: number;
}
export interface ProjectSummary {
  name: string; path: string; session_count: number; usage: Usage;
  cost: number; cost_known: boolean; last_activity: string | null; models: string[];
}
export interface ModelStat {
  model: string; provider: string; usage: Usage; cost: number;
  cost_known: boolean; session_count: number;
}
export interface TimeBucket {
  date: string; session_count: number; usage: Usage; cost: number;
}
export interface Overview {
  session_count: number; total_usage: Usage; total_cost: number;
  cost_known: boolean; by_model: ModelStat[]; by_project: ProjectSummary[];
  timeseries: TimeBucket[];
}
export interface MessageRecord {
  uuid: string | null; parent_uuid: string | null; timestamp: string | null;
  type: string; model: string | null; git_branch: string | null;
  cwd: string | null; cc_version: string | null; usage: Usage;
  tools: string[]; content_kinds: string[];
}

async function get<T>(path: string): Promise<T> {
  const r = await fetch(`${BASE}${path}`);
  if (!r.ok) throw new Error(`${r.status} ${path}`);
  return r.json() as Promise<T>;
}

export const getOverview = () => get<Overview>("/api/overview");
export const getProjects = () => get<ProjectSummary[]>("/api/projects");
export const getProject = (name: string) =>
  get<{ project: ProjectSummary; sessions: SessionSummary[] }>(
    `/api/projects/${encodeURIComponent(name)}`,
  );
export const getSession = (id: string) =>
  get<{ summary: SessionSummary; messages: MessageRecord[] }>(
    `/api/sessions/${encodeURIComponent(id)}`,
  );
