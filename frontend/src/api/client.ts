const BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

export interface Usage {
  input: number; output: number;
  cache_write_5m: number; cache_write_1h: number; cache_read: number;
  web_search: number; web_fetch: number;
}
export interface CostBreakdown {
  input: number; output: number; cache_write: number; cache_read: number;
}
export interface SessionSummary {
  session_id: string; project: string; cwd: string | null; file_path: string;
  ai_title: string | null; started_at: string | null; ended_at: string | null;
  duration_seconds: number | null; is_active: boolean; models: string[];
  provider: string; git_branch: string | null; cc_version: string | null;
  message_count: number; usage: Usage; lines_generated: number;
  cost: number; cost_known: boolean; cost_breakdown: CostBreakdown;
  cache_savings: number;
  tool_counts: Record<string, number>; content_kind_counts: Record<string, number>;
  skipped_lines: number;
  language_counts: Record<string, number>;
  framework_counts: Record<string, number>;
  builtin_tool_counts: Record<string, number>;
  user_tool_counts: Record<string, number>;
  skill_counts: Record<string, number>;
  mcp_server_counts: Record<string, number>;
  subagent_counts: Record<string, number>;
  slash_command_counts: Record<string, number>;
}
export interface ProjectSummary {
  name: string; path: string; session_count: number; usage: Usage;
  lines_generated: number;
  cost: number; cost_known: boolean; cost_breakdown: CostBreakdown;
  last_activity: string | null; models: string[];
  language_counts: Record<string, number>;
  framework_counts: Record<string, number>;
}
export interface ModelStat {
  model: string; provider: string; usage: Usage; cost: number;
  cost_known: boolean; cost_breakdown: CostBreakdown; session_count: number;
}
export interface TimeBucket {
  date: string; session_count: number; usage: Usage; cost: number;
}
export interface Overview {
  session_count: number; total_usage: Usage; total_cost: number;
  cost_known: boolean; cache_savings: number;
  by_model: ModelStat[]; by_project: ProjectSummary[]; timeseries: TimeBucket[];
  tool_counts: Record<string, number>; content_kind_counts: Record<string, number>;
  top_sessions: SessionSummary[];
  language_counts: Record<string, number>;
  framework_counts: Record<string, number>;
  builtin_tool_counts: Record<string, number>;
  user_tool_counts: Record<string, number>;
  skill_counts: Record<string, number>;
  mcp_server_counts: Record<string, number>;
  subagent_counts: Record<string, number>;
  slash_command_counts: Record<string, number>;
}
export interface MessageRecord {
  uuid: string | null; parent_uuid: string | null; timestamp: string | null;
  type: string; model: string | null; git_branch: string | null;
  cwd: string | null; cc_version: string | null; usage: Usage;
  tools: string[]; content_kinds: string[]; lines_generated: number;
  cost: number; cost_known: boolean; cost_breakdown: CostBreakdown;
  languages: string[];
  frameworks: string[];
  skills: string[];
  subagents: string[];
  mcp_servers: string[];
  slash_commands: string[];
}
export interface InstalledTooling {
  skills: string[];
  plugins_installed: string[];
  plugins_enabled: string[];
  mcp_servers: string[];
  hooks: number;
  subagents: string[];
  commands: string[];
}

async function get<T>(path: string): Promise<T> {
  const r = await fetch(`${BASE}${path}`);
  if (!r.ok) throw new Error(`${r.status} ${path}`);
  return r.json() as Promise<T>;
}

export const getConfig = () => get<{ currency: string }>("/api/config");
export const getOverview = () => get<Overview>("/api/overview");
export const getToolingConfig = () => get<InstalledTooling>("/api/tooling-config");
export const getProjects = () => get<ProjectSummary[]>("/api/projects");
export const getProject = (name: string) =>
  get<{ project: ProjectSummary; sessions: SessionSummary[] }>(
    `/api/projects/${encodeURIComponent(name)}`,
  );
export const getSession = (id: string) =>
  get<{ summary: SessionSummary; messages: MessageRecord[] }>(
    `/api/sessions/${encodeURIComponent(id)}`,
  );
