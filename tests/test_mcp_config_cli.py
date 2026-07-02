import json

from typer.testing import CliRunner

from deep_memory.cli import app


runner = CliRunner()


def test_mcp_config_hermes_outputs_reviewable_yaml_snippet():
    result = runner.invoke(app, ["mcp-config", "--agent", "hermes", "--db", "~/.deep-memory/deep-memory.db"])

    assert result.exit_code == 0
    assert "mcp_servers:" in result.output
    assert "deep_memory:" in result.output
    assert "command: \"deep-memory-mcp\"" in result.output
    assert '"--db"' in result.output
    assert '"~/.deep-memory/deep-memory.db"' in result.output
    assert "Review this snippet" in result.output


def test_mcp_config_claude_outputs_command_example():
    result = runner.invoke(app, ["mcp-config", "--agent", "claude", "--db", "~/.deep-memory/deep-memory.db"])

    assert result.exit_code == 0
    assert "claude mcp add deep-memory -- deep-memory-mcp --db ~/.deep-memory/deep-memory.db" in result.output
    assert "does not modify Claude configuration" in result.output


def test_mcp_config_generic_json_contains_command_args_env_and_notes():
    result = runner.invoke(app, ["mcp-config", "--agent", "generic", "--db", "~/.deep-memory/deep-memory.db", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["command"] == "deep-memory-mcp"
    assert payload["args"] == ["--db", "~/.deep-memory/deep-memory.db"]
    assert payload["env"] == {}
    assert "reviewable snippet" in payload["notes"]


def test_mcp_config_defaults_to_machine_local_database_and_deep_memory_mcp():
    result = runner.invoke(app, ["mcp-config", "--agent", "generic", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["command"] == "deep-memory-mcp"
    assert payload["args"] == ["--db", "~/.deep-memory/deep-memory.db"]
