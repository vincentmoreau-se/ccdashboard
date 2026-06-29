from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class Usage(BaseModel):
    input: int = 0
    output: int = 0
    cache_write_5m: int = 0
    cache_write_1h: int = 0
    cache_read: int = 0
    web_search: int = 0
    web_fetch: int = 0

    def add(self, other: "Usage") -> "Usage":
        return Usage(
            input=self.input + other.input,
            output=self.output + other.output,
            cache_write_5m=self.cache_write_5m + other.cache_write_5m,
            cache_write_1h=self.cache_write_1h + other.cache_write_1h,
            cache_read=self.cache_read + other.cache_read,
            web_search=self.web_search + other.web_search,
            web_fetch=self.web_fetch + other.web_fetch,
        )


class CostBreakdown(BaseModel):
    """Per-component cost in display currency. Buckets sum to the scalar cost.

    The two cache-write tiers (5m/1h) are collapsed into ``cache_write``.
    """

    input: float = 0.0
    output: float = 0.0
    cache_write: float = 0.0
    cache_read: float = 0.0

    def add(self, other: "CostBreakdown") -> "CostBreakdown":
        return CostBreakdown(
            input=self.input + other.input,
            output=self.output + other.output,
            cache_write=self.cache_write + other.cache_write,
            cache_read=self.cache_read + other.cache_read,
        )

    def total(self) -> float:
        return self.input + self.output + self.cache_write + self.cache_read


class MessageRecord(BaseModel):
    uuid: str | None = None
    parent_uuid: str | None = None
    message_id: str | None = None
    timestamp: datetime | None = None
    type: str
    model: str | None = None
    git_branch: str | None = None
    cwd: str | None = None
    cc_version: str | None = None
    usage: Usage = Field(default_factory=Usage)
    tools: list[str] = Field(default_factory=list)
    content_kinds: list[str] = Field(default_factory=list)
    lines_generated: int = 0
    cost: float = 0.0
    cost_known: bool = True
    cost_breakdown: CostBreakdown = Field(default_factory=CostBreakdown)
    languages: list[str] = Field(default_factory=list)
    frameworks: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    subagents: list[str] = Field(default_factory=list)
    mcp_servers: list[str] = Field(default_factory=list)
    slash_commands: list[str] = Field(default_factory=list)


class SessionSummary(BaseModel):
    session_id: str
    project: str
    cwd: str | None = None
    file_path: str
    ai_title: str | None = None
    started_at: datetime | None = None
    ended_at: datetime | None = None
    duration_seconds: float | None = None
    is_active: bool = False
    models: list[str] = Field(default_factory=list)
    provider: str = "anthropic"
    git_branch: str | None = None
    cc_version: str | None = None
    message_count: int = 0
    usage: Usage = Field(default_factory=Usage)
    lines_generated: int = 0
    cost: float = 0.0
    cost_known: bool = True
    cost_breakdown: CostBreakdown = Field(default_factory=CostBreakdown)
    cache_savings: float = 0.0
    tool_counts: dict[str, int] = Field(default_factory=dict)
    content_kind_counts: dict[str, int] = Field(default_factory=dict)
    skipped_lines: int = 0
    language_counts: dict[str, int] = Field(default_factory=dict)
    framework_counts: dict[str, int] = Field(default_factory=dict)
    builtin_tool_counts: dict[str, int] = Field(default_factory=dict)
    user_tool_counts: dict[str, int] = Field(default_factory=dict)
    skill_counts: dict[str, int] = Field(default_factory=dict)
    mcp_server_counts: dict[str, int] = Field(default_factory=dict)
    subagent_counts: dict[str, int] = Field(default_factory=dict)
    slash_command_counts: dict[str, int] = Field(default_factory=dict)


class ProjectSummary(BaseModel):
    name: str
    path: str
    session_count: int = 0
    usage: Usage = Field(default_factory=Usage)
    lines_generated: int = 0
    cost: float = 0.0
    cost_known: bool = True
    cost_breakdown: CostBreakdown = Field(default_factory=CostBreakdown)
    last_activity: datetime | None = None
    models: list[str] = Field(default_factory=list)
    language_counts: dict[str, int] = Field(default_factory=dict)
    framework_counts: dict[str, int] = Field(default_factory=dict)


class ModelStat(BaseModel):
    model: str
    provider: str
    usage: Usage = Field(default_factory=Usage)
    cost: float = 0.0
    cost_known: bool = True
    cost_breakdown: CostBreakdown = Field(default_factory=CostBreakdown)
    session_count: int = 0


class TimeBucket(BaseModel):
    date: str
    session_count: int = 0
    usage: Usage = Field(default_factory=Usage)
    cost: float = 0.0


class Overview(BaseModel):
    session_count: int = 0
    total_usage: Usage = Field(default_factory=Usage)
    total_cost: float = 0.0
    cost_known: bool = True
    cache_savings: float = 0.0
    by_model: list[ModelStat] = Field(default_factory=list)
    by_project: list[ProjectSummary] = Field(default_factory=list)
    timeseries: list[TimeBucket] = Field(default_factory=list)
    tool_counts: dict[str, int] = Field(default_factory=dict)
    content_kind_counts: dict[str, int] = Field(default_factory=dict)
    top_sessions: list[SessionSummary] = Field(default_factory=list)
    language_counts: dict[str, int] = Field(default_factory=dict)
    framework_counts: dict[str, int] = Field(default_factory=dict)
    builtin_tool_counts: dict[str, int] = Field(default_factory=dict)
    user_tool_counts: dict[str, int] = Field(default_factory=dict)
    skill_counts: dict[str, int] = Field(default_factory=dict)
    mcp_server_counts: dict[str, int] = Field(default_factory=dict)
    subagent_counts: dict[str, int] = Field(default_factory=dict)
    slash_command_counts: dict[str, int] = Field(default_factory=dict)
