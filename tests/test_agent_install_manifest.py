from pathlib import Path

import json


MANIFEST = Path("docs/agent-install.json")
README = Path("README.md")
GUIDE = Path("docs/AGENT_INSTALL_GUIDE.md")


def test_agent_install_manifest_is_machine_readable_and_complete():
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))

    assert payload["name"] == "deep-memory"
    assert payload["default_db"] == "~/.deep-memory/deep-memory.db"
    assert payload["install"]["source"]["command"]
    assert payload["install"]["package"]["command"]
    assert payload["verify"]["command"] == "deep-memory verify-install ~/.deep-memory/deep-memory.db --json"
    assert payload["connect"]["mcp"]["command"] == "deep-memory-mcp"
    assert payload["connect"]["mcp"]["args"] == ["--db", "~/.deep-memory/deep-memory.db"]
    assert "secrets" in payload["safe_write_policy"]["forbidden_content"]
    assert "raw transcripts" in payload["safe_write_policy"]["forbidden_content"]
    assert "temp status" in payload["safe_write_policy"]["forbidden_content"]
    assert payload["success_report_schema"]["required"] == [
        "success",
        "db",
        "write_ok",
        "search_ok",
        "mcp_import_ok",
    ]


def test_manifest_is_linked_from_install_docs_and_readme():
    readme = README.read_text(encoding="utf-8")
    guide = GUIDE.read_text(encoding="utf-8")

    assert "docs/agent-install.json" in readme
    assert "docs/agent-install.json" in guide
    assert "deep-memory verify-install ~/.deep-memory/deep-memory.db --json" in guide
