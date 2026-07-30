from pathlib import Path


README = Path("README.md")
EN = Path("docs/AGENT_INSTALL_GUIDE.md")
ZH = Path("docs/AGENT_INSTALL_GUIDE.zh-CN.md")


def test_agent_install_guide_uses_machine_local_default_language():
    text = EN.read_text(encoding="utf-8")

    stale = "Use a " + "project-local database by default"
    assert stale not in text
    assert "machine-local database" in text
    assert "verify-install ~/.deep-memory/deep-memory.db --json" in text
    assert "every agent points at the same chosen database" in text
    assert "scope` and `scope_id` keep records bounded" in text


def test_agent_install_guide_explains_mcp_and_skill_are_complementary():
    text = EN.read_text(encoding="utf-8")

    assert "MCP is the tool-call entry point" in text
    assert "behavior policy" in text
    assert "MCP plus the reviewed `deep-memory-agent` skill" in text
    assert "skill-candidates/deep-memory-agent/SKILL.md` is a candidate" in text
    assert "do not let `deep-memory` write directly into another Hermes profile" in text
    assert "skill_manage" in text


def test_agent_install_guide_covers_agent_specific_policy_surfaces():
    text = EN.read_text(encoding="utf-8")

    assert "### Claude Code" in text
    assert "`CLAUDE.md` provides the operating strategy" in text
    assert "### Codex" in text
    assert "`AGENTS.md`" in text
    assert "### OpenCode" in text
    assert "### Hermes" in text
    assert "hermes skills install <skill-id-or-url>" in text


def test_agent_install_guide_documents_mcp_config_generator():
    text = EN.read_text(encoding="utf-8")

    assert "deep-memory mcp-config --agent claude --db ~/.deep-memory/deep-memory.db" in text
    assert "deep-memory mcp-config --agent hermes --db ~/.deep-memory/deep-memory.db" in text
    assert "deep-memory mcp-config --agent generic --db ~/.deep-memory/deep-memory.db --json" in text
    assert "deep-memory-mcp" in text
    assert '["--db", "~/.deep-memory/deep-memory.db"]' in text
    assert "reviewable" in text


def test_agent_install_guide_documents_uv_path_diagnostics_and_keeps_star_optional():
    text = EN.read_text(encoding="utf-8")

    assert "non-interactive agent shells" in text
    assert "command -v uv || ls -l ~/.local/bin/uv ~/.cargo/bin/uv" in text
    assert 'export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"' in text
    assert "Do not hard-code a maintainer's personal path" in text
    assert "## Optional support" in text
    assert text.index("## Optional support") > text.index("## 8. Check the local WebUI")


def test_readme_connect_your_agent_routes_to_authoritative_runtime_docs():
    text = README.read_text(encoding="utf-8")

    assert "## Connect your agent" in text
    assert "deep-memory mcp-config --agent claude --db ~/.deep-memory/deep-memory.db" in text
    assert "deep-memory mcp-config --agent hermes --db ~/.deep-memory/deep-memory.db" in text
    assert "deep-memory mcp-config --agent generic --db ~/.deep-memory/deep-memory.db --json" in text
    assert "docs/AGENT_INSTALL_GUIDE.md" in text
    assert "docs/AGENT_QUICKSTART_MATRIX.md#claude-code" in text
    assert "docs/ADAPTERS.md" in text
    assert "docs/MCP_INTEROPERABILITY.md" in text


def test_contributing_links_first_time_troubleshooting_path():
    text = Path("CONTRIBUTING.md").read_text(encoding="utf-8")
    troubleshooting = Path("docs/TROUBLESHOOTING.md").read_text(encoding="utf-8")

    assert "docs/TROUBLESHOOTING.md" in text
    assert "pytest" in text
    assert "ruff" in text
    assert "uv sync --extra dev" in troubleshooting
    assert "uv sync --extra dev --extra mcp" in troubleshooting
    assert "Runtime CLI is missing" in troubleshooting


def test_chinese_agent_install_guide_matches_review_boundary():
    text = ZH.read_text(encoding="utf-8")

    assert "machine-local 数据库" in text
    assert "verify-install ~/.deep-memory/deep-memory.db --json" in text
    assert "command -v uv || ls -l ~/.local/bin/uv ~/.cargo/bin/uv" in text
    assert "MCP 是 tool-call 入口" in text
    assert "MCP 加上 review 过的 `deep-memory-agent` skill" in text
    assert "不要让 `deep-memory` 自动写入其他 Hermes profile" in text
    assert "`skill-candidates/deep-memory-agent/SKILL.md` 是 candidate" in text
    assert "### OpenCode" in text
    assert "deep-memory mcp-config --agent claude --db ~/.deep-memory/deep-memory.db" in text
    assert "deep-memory mcp-config --agent hermes --db ~/.deep-memory/deep-memory.db" in text
    assert "deep-memory mcp-config --agent generic --db ~/.deep-memory/deep-memory.db --json" in text
    assert "command: \"deep-memory-mcp\"" in text
    assert "## 可选支持" in text
