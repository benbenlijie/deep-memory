from pathlib import Path


README = Path("README.md")
EN = Path("docs/AGENT_INSTALL_GUIDE.md")
ZH = Path("docs/AGENT_INSTALL_GUIDE.zh-CN.md")


def test_agent_install_guide_uses_machine_local_default_language():
    text = EN.read_text(encoding="utf-8")

    stale = "Use a " + "project-local database by default"
    assert stale not in text
    assert "machine-local database" in text
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


def test_readme_connect_your_agent_documents_mcp_config_generator():
    text = README.read_text(encoding="utf-8")

    assert "## Connect your agent" in text
    assert "deep-memory mcp-config --agent claude --db ~/.deep-memory/deep-memory.db" in text
    assert "deep-memory mcp-config --agent hermes --db ~/.deep-memory/deep-memory.db" in text
    assert "deep-memory mcp-config --agent generic --db ~/.deep-memory/deep-memory.db --json" in text
    assert "claude mcp add deep-memory -- deep-memory-mcp --db ~/.deep-memory/deep-memory.db" in text
    assert "command: \"deep-memory-mcp\"" in text


def test_chinese_agent_install_guide_matches_review_boundary():
    text = ZH.read_text(encoding="utf-8")

    assert "machine-local 数据库" in text
    assert "MCP 是 tool-call 入口" in text
    assert "MCP 加上 review 过的 `deep-memory-agent` skill" in text
    assert "不要让 `deep-memory` 自动写入其他 Hermes profile" in text
    assert "`skill-candidates/deep-memory-agent/SKILL.md` 是 candidate" in text
    assert "### OpenCode" in text
    assert "deep-memory mcp-config --agent claude --db ~/.deep-memory/deep-memory.db" in text
    assert "deep-memory mcp-config --agent hermes --db ~/.deep-memory/deep-memory.db" in text
