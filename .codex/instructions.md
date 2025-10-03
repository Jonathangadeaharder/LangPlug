Project: LangPlug – Codex CLI Agent Instructions

Shell/Env

- Use PowerShell for running servers and Python tools on Windows.
- Always activate Backend venv before python/pip/pytest: `. api_venv/Scripts/activate`.
- Work from `Backend/` when running backend tests.

Pathing

- Ensure `PYTHONPATH=.` when invoking pytest so `core` resolves.
- Tests live in `Backend/tests` and `Backend/data`.

Testing

- Prefer in-process tests using fixtures; do not start external servers.
- Mock external services and filesystem; avoid network.

Style

- ASCII-only in Python code/logs; avoid emojis.
- Minimal diffs, match repo style, no unrelated refactors.
