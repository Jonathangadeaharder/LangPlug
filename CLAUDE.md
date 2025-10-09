# DO NOT DELETE: This file is essential for project documentation.

## Project Structure

```
LangPlug/
├── .cache/          # Tool caches (pytest, ruff, mypy, vite)
├── data/            # Application data (databases, downloads, models)
├── deploy/          # Deployment configurations and scripts
├── scripts/         # Development and utility scripts
├── src/
│   ├── backend/     # Python FastAPI backend
│   └── frontend/    # React/TypeScript frontend
└── .venv/           # Python virtual environment (planned)
```

## Core Rules

- Always run the servers with powershell to have the windows setting instead of WSL
- **NEVER use emojis or Unicode characters in Python code** - Windows PowerShell has encoding issues with Unicode characters (🚀, 📊, ✅, ❌, etc.). Always use plain ASCII text like [INFO], [ERROR], [WARN], [GOOD], [POOR] instead
- **ALWAYS activate backend venv before Python/pytest commands** - Use the venv path: `/mnt/c/Users/Jonandrop/IdeaProjects/LangPlug/src/backend/api_venv/Scripts/activate && python -m pytest ...`
- **NO VERSION SUFFIXES IN CODE**: NEVER use \_v2, \_new, \_old, \_temp, \_backup suffixes in filenames or class names. Source control (Git) handles versioning. When replacing code, delete the old version completely. If you need to reference old code, use git history.
- **NO BACKWARD COMPATIBILITY LAYERS**: When refactoring, update ALL dependencies to use the new architecture directly. Do NOT maintain facades, convenience functions, or compatibility layers just for backward compatibility. Update all imports and usages across the codebase to use the new services/modules. Keep the code modern and slim by removing all boilerplate that exists only for backward compatibility. Source control is the safety net, not compatibility layers in production code.
- **NEVER COMMENT OUT CODE**: ALWAYS delete obsolete code completely. Never use comments to "disable" code (e.g., `# old_function()` or `# TODO: uncomment when ready`). If code is not needed, delete it entirely. Source control (Git) is the safety net for retrieving old code if needed. Commented-out code creates confusion, bloats the codebase, and suggests uncertainty. Be decisive: either keep the code active or delete it completely.

## PowerShell Integration Hook (Last Resort)

A PreToolUse hook is configured in `~/.claude/settings.json` that automatically intercepts Python/Node commands and suggests PowerShell-wrapped versions. This hook should be a **last resort** when Claude consistently forgets to use PowerShell commands.

**Preferred approach**: Explicitly request PowerShell commands in prompts
**Hook approach**: Automatic interception and guidance (already configured)

The hook intercepts: `python`, `python3`, `pytest`, `pip`, `npm`, `node`, `npx`
Location: `~/.claude/hooks/powershell_wrapper.py`

## Backend Virtual Environment

**Critical**: All backend Python/pytest commands MUST use the virtual environment:

- Path: `/mnt/c/Users/Jonandrop/IdeaProjects/LangPlug/src/backend/api_venv/Scripts/activate`
- Command pattern: `cd /mnt/c/Users/Jonandrop/IdeaProjects/LangPlug/src/backend && powershell.exe -Command ". api_venv/Scripts/activate; python -m pytest ..."`
- This ensures all dependencies are available and tests run in the correct environment

### Pre-Commit Hook Failures

- Symptom: `Error: "pre-commit" not found. Did you forget to activate your virtualenv?`
- Root cause: Git hooks run outside the activated venv, so the `pre-commit` executable bundled in `api_venv` is missing from `PATH`.
- Prevention:
  - From WSL or Git Bash, run everything through one `powershell.exe` command so activation always happens before git operations:
    ```bash
    cd /mnt/c/Users/Jonandrop/IdeaProjects/LangPlug/src/backend && \
    powershell.exe -Command ". api_venv/Scripts/activate; pip install pre-commit; pre-commit install"
    ```
  - For subsequent commits just reuse the same pattern, chaining whatever action you need after activation, e.g. `...; pre-commit run --all-files` or `...; git commit`.

## LangPlug-Specific Testing Standards

### Critical Test Hygiene Rules

- **NEVER Test Method Existence Only**: Tests that only check if methods exist (`assert hasattr(service, "method_name")`) are shit tests and must be deleted. These tests are worthless because they:
  - Don't test behavior or return values
  - Don't test error handling or edge cases
  - Pass even if methods are completely broken
  - Are redundant if you have actual behavior tests
  - Test implementation details instead of contracts
  - **Delete all tests like**: `test_facade_has_all_public_methods`, `test_service_has_required_methods`, etc.
  - **Proper tests** call methods, pass arguments, and assert on observable behavior and return values
- **NEVER Test for Non-Existent Methods**: Tests that assert the existence of methods that don't exist (`assert hasattr(service, "non_existent_method")`) are absolute test violations. These tests create false positives and mask missing functionality. If a method doesn't exist, delete the test or fix the implementation - never keep assertions for non-existent code.
- **Delete Obsolete Tests Immediately**: When refactoring removes a method or class, delete ALL tests for that functionality. Don't keep tests for deprecated/removed code with skip marks or comments. Clean deletion is the only acceptable approach.

### AI/ML Service Integration Testing Anti-Patterns

**Critical Rules for AI Service Testing**:

- **Factory Bypass Anti-Pattern**: NEVER remove environment variable testing in favor of direct factory calls like `get_service("model-name")` when the intent is to test environment-based configuration - test the full environment→factory→service→functionality chain
- **Model Mismatch Testing Anti-Pattern**: When testing environment configuration like `LANGPLUG_TRANSCRIPTION_SERVICE=whisper-tiny`, test that the environment variable actually changes behavior, don't bypass it with hardcoded factory parameters

### AI Service Testing Best Practices

- **Minimal Functional Tests**: AI service "hello world" tests should be < 10 lines, < 10 seconds, use smallest models, and actually perform the core operation with real input/output validation
- **Graceful Dependency Skipping**: Use `pytest.skip()` when optional AI dependencies (like NeMo) aren't installed rather than failing tests
- **Environment-Specific Models**: Test environment should use fastest/smallest model variants:
  - Transcription: `whisper-tiny` (test) vs larger models (production)
  - Translation: `opus-de-es`, `nllb-distilled-600m` (test) vs full models (production)

### LangPlug Development History

**2025-10 Fail-Fast Migration**: Removed all bare `except:` blocks from chunk processing services (`translation_handler`, `chunk_handler`, `vocabulary` services). System now fails fast with clear errors instead of silently using fallback values that masked transcription/translation failures.

---

**Protected Files**

The following files are considered essential and should not be deleted:

- `AGENTS.md`
- `QWEN.MD.md`
- `GEMINI.md`
- `CLAUDE.md`
