from pathlib import Path


DOC = Path("docs/SKILL_ACTIVATION_LOOP.md")
DEEP_MEMORY_AGENT_SKILL = Path("skill-candidates/deep-memory-agent/SKILL.md")


def test_skill_activation_loop_doc_defines_required_review_boundaries():
    text = DOC.read_text(encoding="utf-8")

    assert "Auto-install: no" in text
    assert "candidate/review mode" in text
    assert "Trigger conditions" in text
    assert "Evidence requirements" in text
    assert "Review gate" in text
    assert "Installation boundary" in text
    assert "Rollback" in text


def test_skill_activation_loop_doc_has_end_to_end_example():
    text = DOC.read_text(encoding="utf-8")

    assert "End-to-end example" in text
    assert "Procedural memory" in text
    assert "Skill candidate markdown" in text
    assert "Human review checklist" in text
    assert "Agent usage after approved installation" in text
    assert "procedural_memory_to_skill_markdown" in text


def test_skill_activation_loop_doc_keeps_installation_outside_export_prototype():
    text = DOC.read_text(encoding="utf-8")

    assert "Installation is outside the export prototype" in text
    assert "Candidates should not install themselves" in text
    assert "safe default target is a review directory" in text


def test_deep_memory_agent_skill_candidate_exists_with_safety_boundaries():
    text = DEEP_MEMORY_AGENT_SKILL.read_text(encoding="utf-8")

    assert text.startswith("---\n")
    frontmatter = text.split("\n---\n", 1)[0]
    assert "name: deep-memory-agent" in frontmatter
    assert "description:" in frontmatter
    assert "Auto-install: no" in text
    assert "review required" in text
    assert "When to use" in text
    assert "When not to use" in text
    assert "deep-memory search" in text
    assert "deep-memory add" in text
    assert "deep-memory webui" in text
    assert "~/.deep-memory/deep-memory.db" in text
    assert "scope_id" in text
    assert "secrets" in text
    assert "raw transcript" in text
    assert "unverified speculation" in text
    assert "stale task IDs" in text
    assert "Rollback" in text
