from pathlib import Path


PACKAGING = Path("docs/PACKAGING.md")
README = Path("README.md")
PYPROJECT = Path("pyproject.toml")


def test_packaging_doc_covers_build_local_install_and_release_boundaries():
    text = PACKAGING.read_text(encoding="utf-8")

    assert "uv build" in text
    assert "uv tool install" in text
    assert "deep-memory verify-install ~/.deep-memory/deep-memory.db --json" in text
    assert "deep-memory-mcp" in text
    assert "Do not publish to PyPI without explicit maintainer approval" in text
    assert "GitHub Release" in text
    assert "PyPI" in text


def test_pyproject_exposes_expected_console_scripts_and_package_metadata():
    text = PYPROJECT.read_text(encoding="utf-8")

    assert 'name = "deep-memory"' in text
    assert 'deep-memory = "deep_memory.cli:app"' in text
    assert 'deep-memory-mcp = "deep_memory.mcp_server:main"' in text
    assert 'mcp = ["mcp>=1.0.0"]' in text


def test_readme_links_packaging_doc_for_package_install_path():
    assert "docs/PACKAGING.md" in README.read_text(encoding="utf-8")
