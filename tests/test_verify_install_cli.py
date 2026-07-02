import json

from typer.testing import CliRunner

from deep_memory.cli import app


runner = CliRunner()


def test_verify_install_json_initializes_writes_searches_and_cleans_up(tmp_path):
    db = tmp_path / "deep-memory.db"

    result = runner.invoke(app, ["verify-install", str(db), "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["success"] is True
    assert payload["db"] == str(db)
    assert payload["cli_ok"] is True
    assert payload["db_ok"] is True
    assert payload["write_ok"] is True
    assert payload["search_ok"] is True
    assert payload["cleanup_ok"] is True
    assert payload["scope"] == "workspace"
    assert payload["scope_id"] == "verify-install"
    assert payload["record_id"]
    assert payload["mcp_import_ok"] is True
    assert payload["errors"] == []

    second = runner.invoke(app, ["search", str(db), "deep-memory verify-install smoke", "--all-scopes"])
    assert "deep-memory verify-install smoke" not in second.output


def test_verify_install_human_output_reports_success(tmp_path):
    db = tmp_path / "deep-memory.db"

    result = runner.invoke(app, ["verify-install", str(db)])

    assert result.exit_code == 0, result.output
    assert "deep-memory install verification succeeded" in result.output
    assert str(db) in result.output
    assert "write_ok=True" in result.output
    assert "search_ok=True" in result.output


def test_verify_install_rejects_existing_directory_path(tmp_path):
    result = runner.invoke(app, ["verify-install", str(tmp_path), "--json"])

    assert result.exit_code != 0
    assert "database path points to a directory" in result.output
