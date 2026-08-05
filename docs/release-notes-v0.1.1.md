# Release notes draft — v0.1.1

Status: release candidate. Publish to TestPyPI and PyPI only after the documented clean-install gates pass and a maintainer explicitly approves each upload.

## Highlights

- Restores the declared Python 3.10 compatibility by replacing the Python 3.11-only `enum.StrEnum` dependency with a string-valued `Enum` implementation.
- Constrains the optional MCP dependency to the compatible `mcp>=1.0.0,<2` API line so a clean install does not resolve to the incompatible MCP 2.x package.
- Expands CI to Python 3.10, 3.11, and 3.12 with the MCP extra installed on every test lane.
- Adds a package gate that builds the wheel and sdist, validates metadata, installs the wheel in a clean environment, runs `verify-install`, and exercises `add`, `search`, and `stats` through a real MCP stdio client.
- Adds PyPI project links for the repository, issue tracker, documentation, and homepage.

## Verification contract

Before the PyPI upload, the release must prove:

1. the full pytest suite passes on Python 3.10, 3.11, and 3.12;
2. Ruff and `uv lock --check` pass;
3. `uv build` produces `deep_memory-0.1.1.tar.gz` and `deep_memory-0.1.1-py3-none-any.whl`;
4. `twine check` passes for both artifacts;
5. a clean wheel install with `[mcp]` passes `deep-memory verify-install ... --json`;
6. a real MCP stdio client initializes, lists tools, and successfully calls `add`, `search`, and `stats`;
7. the same install and MCP gates pass from TestPyPI.

After the explicitly approved PyPI upload, repeat the clean-install and MCP gates
against PyPI. Publish the GitHub Release only after that post-upload verification passes.

## Evaluation snapshot

- Chinese retrieval v1: 55/55.
- Chinese retrieval v2: 20/20.
- Memory benchmark v0: no-memory baseline 0/20; deep-memory 18/20 with the default retrieval limit in the current checked-in run.

These are repository regression fixtures, not a claim that general agent memory is solved.

## Safety boundaries

- No automatic TestPyPI or PyPI upload.
- TestPyPI and PyPI require separate credentials and explicit maintainer approval.
- Create the GitHub Release as a draft before package publication; publish it only after the PyPI clean-install and MCP gates pass.
- Create and verify the final signed tag from the merged release commit.