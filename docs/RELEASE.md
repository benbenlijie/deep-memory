# Release checklist

This project is not published automatically from local machines. Treat every release as a small, auditable loop: validate metadata, build artifacts from a clean tree, check the distribution, then publish only with explicit PyPI credentials.

## 1. Preconditions

- Confirm the working tree is clean except for intentional release changes:

  ```bash
  git status --short
  ```

- Confirm the version in `pyproject.toml` is the version you intend to release.
- Confirm `README.md` still states the correct installation status. Before the first PyPI release, it should not tell users to `pip install deep-memory`.
- Confirm local quality gates pass:

  ```bash
  uv sync --extra dev
  uv run ruff check .
  uv run pytest
  ```

## 2. Validate package metadata and build locally

Build the source distribution and wheel:

```bash
rm -rf dist/
uv build
```

Expected artifact shape for version `0.1.0`:

```text
dist/deep_memory-0.1.0.tar.gz
dist/deep_memory-0.1.0-py3-none-any.whl
```

Check that PyPI will accept the distribution metadata:

```bash
uvx twine check dist/*
```

The check should report `PASSED` for both the wheel and sdist.

## 3. Dry-run publish to TestPyPI

Use TestPyPI before real PyPI. This requires a TestPyPI API token in `TWINE_PASSWORD`; do not commit tokens to the repository.

```bash
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=<testpypi-api-token>
uvx twine upload --repository testpypi dist/*
```

Then test installation from TestPyPI in a fresh environment:

```bash
uv venv /tmp/deep-memory-testpypi
/tmp/deep-memory-testpypi/bin/python -m pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ deep-memory==0.1.0
/tmp/deep-memory-testpypi/bin/deep-memory --help
```

## 4. Publish to PyPI

Only publish after the TestPyPI install check passes and a maintainer explicitly approves the release.

```bash
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=<pypi-api-token>
uvx twine upload dist/*
```

## 5. Post-release verification

After PyPI upload completes:

```bash
uv venv /tmp/deep-memory-pypi
/tmp/deep-memory-pypi/bin/python -m pip install deep-memory==0.1.0
/tmp/deep-memory-pypi/bin/deep-memory --help
```

Then update `README.md` to replace the source-only install note with the PyPI install path, if this was the first public release.

## Current release blocker

Local build and metadata validation can run without credentials. Publishing is blocked unless the operator provides PyPI/TestPyPI API tokens via `TWINE_PASSWORD` and explicitly approves upload. Do not publish from automation without that approval.
