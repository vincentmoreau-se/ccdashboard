"""
Shared classification tables and functions for taxonomy of languages, frameworks,
and Claude Code tools. Pure module — no I/O, no external dependencies.
"""
from __future__ import annotations

import os

# ---------------------------------------------------------------------------
# Data tables
# ---------------------------------------------------------------------------

EXTENSION_LANGUAGE: dict[str, str] = {
    ".py": "Python",
    ".ts": "TypeScript",
    ".tsx": "TypeScript/React",
    ".js": "JavaScript",
    ".jsx": "JavaScript/React",
    ".go": "Go",
    ".rs": "Rust",
    ".java": "Java",
    ".rb": "Ruby",
    ".php": "PHP",
    ".c": "C",
    ".h": "C",
    ".cpp": "C++",
    ".cc": "C++",
    ".cs": "C#",
    ".kt": "Kotlin",
    ".swift": "Swift",
    ".sh": "Shell",
    ".bash": "Shell",
    ".sql": "SQL",
    ".md": "Markdown",
    ".yml": "YAML",
    ".yaml": "YAML",
    ".json": "JSON",
    ".toml": "TOML",
    ".html": "HTML",
    ".css": "CSS",
    ".scss": "CSS",
}

MANIFEST_FRAMEWORK: dict[str, str] = {
    "package.json": "Node.js",
    "pnpm-lock.yaml": "Node.js",
    "yarn.lock": "Node.js",
    "pyproject.toml": "Python",
    "requirements.txt": "Python",
    "setup.py": "Python",
    "pipfile": "Python",
    "cargo.toml": "Rust",
    "go.mod": "Go",
    "pom.xml": "Java/Maven",
    "build.gradle": "Gradle",
    "gemfile": "Ruby",
    "composer.json": "PHP",
    "dockerfile": "Docker",
    "docker-compose.yml": "Docker",
    "tsconfig.json": "TypeScript",
    "go.sum": "Go",
}

COMMAND_FRAMEWORK: dict[str, str] = {
    "npm": "Node.js",
    "npx": "Node.js",
    "pnpm": "Node.js",
    "yarn": "Node.js",
    "uv": "Python",
    "pip": "Python",
    "pip3": "Python",
    "poetry": "Python",
    "ruff": "Python",
    "black": "Python",
    "pytest": "pytest",
    "vite": "Vite",
    "cargo": "Rust",
    "go": "Go",
    "docker": "Docker",
    "docker-compose": "Docker",
    "tsc": "TypeScript",
    "playwright": "Playwright",
}

BUILTIN_TOOLS: frozenset[str] = frozenset({
    "Bash",
    "BashOutput",
    "KillShell",
    "Read",
    "Write",
    "Edit",
    "MultiEdit",
    "NotebookEdit",
    "Glob",
    "Grep",
    "Task",
    "Agent",
    "TodoWrite",
    "TaskCreate",
    "TaskUpdate",
    "TaskList",
    "TaskGet",
    "TaskStop",
    "TaskOutput",
    "WebFetch",
    "WebSearch",
    "ToolSearch",
    "ExitPlanMode",
    "AskUserQuestion",
    "SendMessage",
    "ScheduleWakeup",
    "RemoteTrigger",
    "SlashCommand",
})

BUILTIN_SUBAGENTS: frozenset[str] = frozenset({"general-purpose", "Explore", "Plan"})

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_PREFIX_FRAMEWORKS: list[tuple[str, str]] = [
    ("vite.config.", "Vite"),
    ("tailwind.config.", "Tailwind"),
    ("playwright.config.", "Playwright"),
]

# ---------------------------------------------------------------------------
# Classification functions
# ---------------------------------------------------------------------------


def language_for_path(path: str) -> str | None:
    """Return the language name for the given file path, or None."""
    if not path:
        return None
    _, ext = os.path.splitext(path)
    if not ext:
        return None
    return EXTENSION_LANGUAGE.get(ext.lower())


def framework_for_manifest(path: str) -> str | None:
    """Return the framework/ecosystem for a manifest file path, or None."""
    if not path:
        return None
    basename = os.path.basename(path).lower()
    # Exact match first
    if basename in MANIFEST_FRAMEWORK:
        return MANIFEST_FRAMEWORK[basename]
    # Prefix-based detection for config files with variable suffixes
    for prefix, framework in _PREFIX_FRAMEWORKS:
        if basename.startswith(prefix):
            return framework
    return None


def frameworks_for_command(command: str) -> list[str]:
    """Return a deduplicated, order-preserving list of frameworks implied by command tokens."""
    if not command:
        return []
    seen: dict[str, None] = {}  # ordered set via insertion-ordered dict
    for token in command.split():
        fw = COMMAND_FRAMEWORK.get(token.lower())
        if fw is not None:
            seen[fw] = None
    return list(seen.keys())


def classify_tool(name: str) -> str:
    """Classify a tool name as 'mcp', 'skill', 'builtin', or 'other'."""
    if name.startswith("mcp__"):
        return "mcp"
    if name == "Skill":
        return "skill"
    if name in BUILTIN_TOOLS:
        return "builtin"
    return "other"


def mcp_server_of(name: str) -> str | None:
    """Extract the MCP server name from an mcp__<server>__<tool> tool name, or None."""
    parts = name.split("__")
    if len(parts) >= 3 and parts[0] == "mcp":
        return parts[1]
    return None


def is_builtin_subagent(subagent_type: str) -> bool:
    """Return True if subagent_type is a built-in Claude Code subagent."""
    return subagent_type in BUILTIN_SUBAGENTS
