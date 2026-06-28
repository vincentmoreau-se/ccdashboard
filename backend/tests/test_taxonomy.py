from app.taxonomy import (
    classify_tool,
    framework_for_manifest,
    frameworks_for_command,
    is_builtin_subagent,
    language_for_path,
    mcp_server_of,
)


# ---------------------------------------------------------------------------
# classify_tool
# ---------------------------------------------------------------------------


def test_classify_tool_builtin():
    assert classify_tool("Bash") == "builtin"


def test_classify_tool_skill():
    assert classify_tool("Skill") == "skill"


def test_classify_tool_mcp():
    assert classify_tool("mcp__playwright__browser_navigate") == "mcp"


def test_classify_tool_other():
    assert classify_tool("MyCustomTool") == "other"


# ---------------------------------------------------------------------------
# language_for_path
# ---------------------------------------------------------------------------


def test_language_for_path_python():
    assert language_for_path("app/x.py") == "Python"


def test_language_for_path_tsx():
    assert language_for_path("src/App.tsx") == "TypeScript/React"


def test_language_for_path_unknown_ext():
    assert language_for_path("a.unknownext") is None


def test_language_for_path_no_ext():
    assert language_for_path("Makefile") is None


def test_language_for_path_empty():
    assert language_for_path("") is None


def test_language_for_path_case_insensitive():
    assert language_for_path("script.PY") == "Python"


# ---------------------------------------------------------------------------
# framework_for_manifest
# ---------------------------------------------------------------------------


def test_framework_for_manifest_package_json():
    assert framework_for_manifest("package.json") == "Node.js"


def test_framework_for_manifest_pyproject_toml_with_subdir():
    assert framework_for_manifest("sub/pyproject.toml") == "Python"


def test_framework_for_manifest_vite_config_ts():
    assert framework_for_manifest("frontend/vite.config.ts") == "Vite"


def test_framework_for_manifest_vite_config_js():
    assert framework_for_manifest("vite.config.js") == "Vite"


def test_framework_for_manifest_tailwind_config():
    assert framework_for_manifest("tailwind.config.cjs") == "Tailwind"


def test_framework_for_manifest_playwright_config():
    assert framework_for_manifest("playwright.config.ts") == "Playwright"


def test_framework_for_manifest_unknown():
    assert framework_for_manifest("foo.txt") is None


def test_framework_for_manifest_empty():
    assert framework_for_manifest("") is None


# ---------------------------------------------------------------------------
# frameworks_for_command
# ---------------------------------------------------------------------------


def test_frameworks_for_command_npm():
    result = frameworks_for_command("npm run build")
    assert "Node.js" in result


def test_frameworks_for_command_uv_pytest():
    result = frameworks_for_command("uv run pytest")
    assert "Python" in result
    assert "pytest" in result


def test_frameworks_for_command_empty_string():
    assert frameworks_for_command("") == []


def test_frameworks_for_command_none_like():
    # Ensure no crash on falsy input
    assert frameworks_for_command("") == []


def test_frameworks_for_command_deduplicates():
    # npm appears twice but should only produce one "Node.js"
    result = frameworks_for_command("npm run && npx foo")
    assert result.count("Node.js") == 1


def test_frameworks_for_command_preserves_order():
    result = frameworks_for_command("uv run pytest")
    assert result.index("Python") < result.index("pytest")


# ---------------------------------------------------------------------------
# mcp_server_of
# ---------------------------------------------------------------------------


def test_mcp_server_of_valid():
    assert mcp_server_of("mcp__playwright__browser_navigate") == "playwright"


def test_mcp_server_of_non_mcp():
    assert mcp_server_of("Bash") is None


def test_mcp_server_of_incomplete():
    # Only two parts — not enough to extract a server
    assert mcp_server_of("mcp__playwright") is None


# ---------------------------------------------------------------------------
# is_builtin_subagent
# ---------------------------------------------------------------------------


def test_is_builtin_subagent_true():
    assert is_builtin_subagent("general-purpose") is True
    assert is_builtin_subagent("Explore") is True
    assert is_builtin_subagent("Plan") is True


def test_is_builtin_subagent_false():
    assert is_builtin_subagent("my-custom-agent") is False
