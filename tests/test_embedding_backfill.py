from typer.testing import CliRunner

from deep_memory import DeepMemory
from deep_memory.cli import app
from deep_memory.embeddings import DeterministicEmbeddingBackend


class CountingEmbeddingBackend(DeterministicEmbeddingBackend):
    def __init__(self, *, model_name: str = "backfill-test", model_version: int = 1, dim: int = 8) -> None:
        super().__init__(model_name=model_name, model_version=model_version, dim=dim)
        self.batch_sizes: list[int] = []
        self.texts: list[str] = []

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        self.batch_sizes.append(len(texts))
        self.texts.extend(texts)
        return super().embed_batch(texts)


def test_backfill_embeddings_dry_run_counts_missing_without_writes(tmp_path):
    db = tmp_path / "memory.db"
    mem = DeepMemory(db)
    for idx in range(100):
        mem.add(f"memory needing embedding {idx}", kind="semantic")

    result = mem.backfill_embeddings(embedding_backend=CountingEmbeddingBackend(), batch_size=25, dry_run=True)

    assert result.scanned == 100
    assert result.backfilled == 0
    assert result.skipped == 0
    assert result.dry_run is True
    assert mem.conn.execute("SELECT COUNT(*) FROM memory_embeddings").fetchone()[0] == 0
    assert mem.conn.execute("SELECT COUNT(*) FROM memories WHERE embedding_model IS NULL").fetchone()[0] == 100


def test_backfill_embeddings_batches_100_memories_and_is_idempotent(tmp_path):
    mem = DeepMemory(tmp_path / "memory.db")
    for idx in range(100):
        mem.add(f"batch backfill memory {idx}", kind="semantic")
    backend = CountingEmbeddingBackend(model_name="batch-model", model_version=3, dim=6)

    first = mem.backfill_embeddings(embedding_backend=backend, batch_size=30)
    second = mem.backfill_embeddings(embedding_backend=backend, batch_size=30)

    assert first.scanned == 100
    assert first.backfilled == 100
    assert first.skipped == 0
    assert backend.batch_sizes == [30, 30, 30, 10]
    assert second.scanned == 100
    assert second.backfilled == 0
    assert second.skipped == 100
    rows = mem.conn.execute(
        "SELECT COUNT(*), MIN(model_name), MIN(model_version), MIN(dim) FROM memory_embeddings"
    ).fetchone()
    assert tuple(rows) == (100, "batch-model", 3, 6)
    assert mem.conn.execute("SELECT COUNT(*) FROM memories WHERE embedding_model = 'batch-model'").fetchone()[0] == 100


def test_backfill_embeddings_resumes_after_partial_existing_embeddings(tmp_path):
    mem = DeepMemory(tmp_path / "memory.db")
    records = [mem.add(f"resume backfill memory {idx}", kind="semantic") for idx in range(100)]
    backend = CountingEmbeddingBackend(model_name="resume-model", model_version=2, dim=5)

    for record in records[:40]:
        mem._store_embedding(record.id, record.content, backend)  # exercise interrupted-run state
    mem.conn.commit()
    resumed = mem.backfill_embeddings(embedding_backend=backend, batch_size=25)

    assert resumed.scanned == 100
    assert resumed.skipped == 40
    assert resumed.backfilled == 60
    assert backend.batch_sizes == [25, 25, 10]
    assert mem.conn.execute("SELECT COUNT(*) FROM memories WHERE embedding_version = 2").fetchone()[0] == 100


def test_search_vector_mode_filters_by_embedding_version(tmp_path):
    mem = DeepMemory(tmp_path / "memory.db")
    old_backend = CountingEmbeddingBackend(model_name="version-model", model_version=1, dim=4)
    new_backend = CountingEmbeddingBackend(model_name="version-model", model_version=2, dim=4)
    old = mem.add("old vector generation about release", kind="semantic")
    new = mem.add("new vector generation about release", kind="semantic")
    mem._store_embedding(old.id, old.content, old_backend)
    mem._store_embedding(new.id, new.content, new_backend)
    mem.conn.commit()
    mem._embedding_backend = new_backend
    mem._embedding_backend_resolved = True

    results = mem.search("release", retrieval_mode="vector", embedding_version=2, cross_workspace=True, limit=1)

    assert [result.record.id for result in results] == [new.id]


def test_cli_backfill_embeddings_dry_run_and_batch_size(tmp_path, monkeypatch):
    db = tmp_path / "memory.db"
    mem = DeepMemory(db)
    for idx in range(3):
        mem.add(f"cli backfill memory {idx}", kind="semantic")
    mem.close()
    monkeypatch.setenv("DEEP_MEMORY_EMBEDDING", "on")
    monkeypatch.setattr("deep_memory.core.get_default_embedding_backend", lambda: CountingEmbeddingBackend())

    result = CliRunner().invoke(app, ["backfill-embeddings", str(db), "--batch-size", "2", "--dry-run"])

    assert result.exit_code == 0
    assert "would backfill 3 embeddings" in result.output
    assert "batch_size=2" in result.output
    check = DeepMemory(db)
    assert check.conn.execute("SELECT COUNT(*) FROM memory_embeddings").fetchone()[0] == 0
