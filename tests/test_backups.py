from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from typer.testing import CliRunner

from deep_memory import DeepMemory
from deep_memory.cli import app
from deep_memory.core import BackupError


def _add_similar_records(mem: DeepMemory, count: int = 5) -> None:
    for idx in range(count):
        mem.add(f"项目事实：alpha beta gamma delta {idx}", kind="semantic")


def test_consolidate_creates_db_backup_with_manifest_before_destructive_write(tmp_path):
    db = tmp_path / "deep-memory.db"
    mem = DeepMemory(db)
    _add_similar_records(mem)

    plan = mem.consolidate(dry_run=False, threshold=0.6)

    assert plan.created_count > 0
    backups = [
        path
        for path in sorted((tmp_path / "deep-memory.db.backups").glob("deep-memory.db.bak-*"))
        if not path.name.endswith(".manifest.json")
    ]
    assert len(backups) == 1
    backup = backups[0]
    assert sqlite3.connect(backup).execute("SELECT COUNT(*) FROM memories").fetchone()[0] == 5
    manifest = json.loads(backup.with_suffix(backup.suffix + ".manifest.json").read_text(encoding="utf-8"))
    assert manifest["trigger_reason"] == "consolidate"
    assert manifest["source_db_size"] == db.stat().st_size
    assert manifest["record_count"] == 5
    assert datetime.fromisoformat(manifest["created_at"])


def test_prune_backups_removes_expired_backup_and_manifest(tmp_path):
    db = tmp_path / "deep-memory.db"
    mem = DeepMemory(db)
    mem.add("keep db non-empty")
    backup = mem.create_backup("test-old")
    old_time = (datetime.now(timezone.utc) - timedelta(days=8)).timestamp()
    os.utime(backup, (old_time, old_time))
    os.utime(backup.with_suffix(backup.suffix + ".manifest.json"), (old_time, old_time))

    result = mem.prune_backups(retention_days=7)

    assert result["deleted"] == [str(backup)]
    assert not backup.exists()
    assert not backup.with_suffix(backup.suffix + ".manifest.json").exists()


def test_backup_retention_days_zero_skips_backup_for_development(tmp_path):
    db = tmp_path / "deep-memory.db"
    mem = DeepMemory(db, backup_retention_days=0)
    _add_similar_records(mem)

    plan = mem.consolidate(dry_run=False, threshold=0.6)

    assert plan.created_count > 0
    assert not (tmp_path / "deep-memory.db.backups").exists()


def test_backup_failure_aborts_destructive_operation_without_changing_original_db(tmp_path, monkeypatch):
    db = tmp_path / "deep-memory.db"
    mem = DeepMemory(db)
    _add_similar_records(mem)
    before_ids = [record.id for record in mem.export_records(include_deprecated=True)]

    def fail_backup(_reason: str) -> Path:
        raise BackupError("unable to create DB backup before consolidate: disk full")

    monkeypatch.setattr(mem, "create_backup", fail_backup)

    with pytest.raises(BackupError, match="disk full"):
        mem.consolidate(dry_run=False, threshold=0.6)

    after_records = mem.export_records(include_deprecated=True)
    assert [record.id for record in after_records] == before_ids
    assert all(record.conflict_status == "active" for record in after_records)


def test_hard_delete_creates_backup_before_removing_record(tmp_path):
    db = tmp_path / "deep-memory.db"
    mem = DeepMemory(db)
    record = mem.add("删除前必须备份")

    deleted = mem.hard_delete(record.id)

    assert deleted == 1
    backups = [
        path
        for path in sorted((tmp_path / "deep-memory.db.backups").glob("deep-memory.db.bak-*"))
        if not path.name.endswith(".manifest.json")
    ]
    assert len(backups) == 1
    assert sqlite3.connect(backups[0]).execute("SELECT COUNT(*) FROM memories").fetchone()[0] == 1
    manifest = json.loads(backups[0].with_suffix(backups[0].suffix + ".manifest.json").read_text(encoding="utf-8"))
    assert manifest["trigger_reason"] == "hard_delete"


def test_prune_backups_cli_dry_run_reports_without_deleting(tmp_path):
    db = tmp_path / "deep-memory.db"
    mem = DeepMemory(db)
    mem.add("keep db non-empty")
    backup = mem.create_backup("test-old")
    old_time = (datetime.now(timezone.utc) - timedelta(days=8)).timestamp()
    os.utime(backup, (old_time, old_time))

    result = CliRunner().invoke(app, ["prune-backups", str(db), "--dry-run"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["dry_run"] is True
    assert str(backup) in payload["expired"]
    assert backup.exists()
