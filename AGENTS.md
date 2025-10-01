# DO NOT DELETE: This file is essential for project documentation.

Codex CLI Agent Guidelines for LangPlug

Scope

- Applies to entire repository.

Operating System and Shell

- Prefer Windows PowerShell for running servers and Python tools from the host OS.
- When issuing Python/pytest/pip commands, always activate the Backend venv first.
- Use WSL only for light file ops; avoid mixing environments for runtime tasks.

Backend Virtual Environment

- Activation path: /mnt/c/Users/Jonandrop/IdeaProjects/LangPlug/Backend/api_venv/Scripts/activate
- Command pattern: cd /mnt/c/Users/Jonandrop/IdeaProjects/LangPlug/Backend && powershell.exe -Command ". api_venv/Scripts/activate; python -m pytest ..."

Language and Encoding

- Do not use emojis or non-ASCII in Python code or logs. Use ASCII tags like [INFO], [ERROR], [WARN].

Testing Conventions

- Use in-process FastAPI clients and dependency overrides (see Backend/tests/conftest.py).
- Mock external services (Redis, transcription) and filesystem paths; do not hit network or disk.
- Align test assertions with behavior rather than exact error message text when messages vary.

Architecture Notes

- Core backend modules live under Backend/core, services under Backend/services, API routes under Backend/api.
- Database access via core.database AsyncSessionLocal and get_async_session dependency.
- Prefer background tasks via FastAPI BackgroundTasks with explicit signatures; keep mocks in sync with interfaces.

Coding Style

- Keep changes minimal and focused; do not refactor unrelated code.
- Follow existing naming and structure; no one-letter variables.
- Avoid inline comments unless necessary for clarity.

Workflow

- For large changes, propose a short stepwise plan; update as you progress.
- Validate with targeted pytest runs in the venv; then broader suite.

---

**Protected Files**

The following files are considered essential and should not be deleted:

- `AGENTS.md`
- `QWEN.MD.md`
- `GEMINI.md`
- `CLAUDE.md`
