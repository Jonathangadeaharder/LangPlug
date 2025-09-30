# DO NOT DELETE: This file is essential for project documentation.
- Always run the servers with powershell to have the windows setting instead of WSL
- **NEVER use emojis or Unicode characters in Python code** - Windows PowerShell has encoding issues with Unicode characters (🚀, 📊, ✅, ❌, etc.). Always use plain ASCII text like [INFO], [ERROR], [WARN], [GOOD], [POOR] instead
- **ALWAYS activate Backend venv before Python/pytest commands** - Use the venv path: `/mnt/c/Users/Jonandrop/IdeaProjects/LangPlug/Backend/api_venv/Scripts/activate && python -m pytest ...`
- **NO VERSION SUFFIXES IN CODE**: NEVER use _v2, _new, _old, _temp, _backup suffixes in filenames or class names. Source control (Git) handles versioning. When replacing code, delete the old version completely. If you need to reference old code, use git history.
- **NO BACKWARD COMPATIBILITY LAYERS**: When refactoring, update ALL dependencies to use the new architecture directly. Do NOT maintain facades, convenience functions, or compatibility layers just for backward compatibility. Update all imports and usages across the codebase to use the new services/modules. Keep the code modern and slim by removing all boilerplate that exists only for backward compatibility. Source control is the safety net, not compatibility layers in production code.

## PowerShell Integration Hook (Last Resort)

A PreToolUse hook is configured in `~/.claude/settings.json` that automatically intercepts Python/Node commands and suggests PowerShell-wrapped versions. This hook should be a **last resort** when Claude consistently forgets to use PowerShell commands.

**Preferred approach**: Explicitly request PowerShell commands in prompts
**Hook approach**: Automatic interception and guidance (already configured)

The hook intercepts: `python`, `python3`, `pytest`, `pip`, `npm`, `node`, `npx`
Location: `~/.claude/hooks/powershell_wrapper.py`

## Backend Virtual Environment
**Critical**: All Backend Python/pytest commands MUST use the virtual environment:
- Path: `/mnt/c/Users/Jonandrop/IdeaProjects/LangPlug/Backend/api_venv/Scripts/activate`
- Command pattern: `cd /mnt/c/Users/Jonandrop/IdeaProjects/LangPlug/Backend && powershell.exe -Command ". api_venv/Scripts/activate; python -m pytest ..."`
- This ensures all dependencies are available and tests run in the correct environment

---
**Protected Files**

The following files are considered essential and should not be deleted:
- `AGENTS.md`
- `QWEN.MD.md`
- `GEMINI.md`
- `CLAUDE.md`
