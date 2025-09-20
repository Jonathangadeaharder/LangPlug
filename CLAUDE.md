# DEPRECATED: Claude AI Assistant Instructions for LangPlug

**⚠️ DEPRECATION NOTICE**: This file has been consolidated into the unified AI Development Guide.

**👉 Use instead**: `AI_DEVELOPMENT_GUIDE.md` - Comprehensive guide for all AI coding assistants

---

- always execute python with api_venv
- on WSL, run .bat files using: cmd.exe /c filename.bat (not ./filename.bat)
- to properly clean up hanging CMD processes: cmd.exe /c "taskkill /F /IM cmd.exe && taskkill /F /IM python.exe && taskkill /F /IM node.exe"
- always use browsermcp when you want to verify end to end behaviour together with reading the logs
- whenever you fail an action or tool use and later find out how to do it correctly, update this file with the lesson learned
- **IMPORTANT**: Always use `cmd.exe /c start.bat` to start both frontend and backend servers - this script handles necessary cleanup and proper initialization. Never start servers manually.

# lessons-learned-2025-09-07
- Server startup should use dynamic polling instead of fixed timeouts - backend takes ~25s due to Whisper model loading
- On Windows, npm commands need to be run with cmd.exe /c prefix for proper execution
- Health checks should poll every 2 seconds with informative progress messages

# lessons-learned-2025-09-16
- In WSL, Windows Python executables must be accessed via mount points like /mnt/e/path/to/python.exe
- Cannot run Windows python.exe directly from WSL bash without proper mount path
- Windows venv created on E: drive should be executed as: /mnt/e/Users/Jonandrop/IdeaProjects/LangPlug/Backend/api_venv/Scripts/python.exe
- WSL file system /mnt/ represents mounted Windows drives (e.g., C:\ = /mnt/c/, E:\ = /mnt/e/)
- FastAPI-Users login expects form data (not JSON) and email address in username field
- FastAPI-Users Bearer transport returns {"access_token": "...", "token_type": "bearer"} (no user data in login response)
- Tests expecting wrong FastAPI-Users response format should be updated to match actual API behavior
- Modern test infrastructure: Use transaction rollback for test isolation, standardized auth helpers, and proper fixture patterns
- Test infrastructure problems can be prevented by following patterns in TESTING_BEST_PRACTICES.md and tests/conftest.py
- FastAPI-Users UserManager requires parse_id() method implementation for UUID handling

# lessons-learned-2025-09-19
- PowerShell 7 at '/mnt/c/Program Files/PowerShell/7/pwsh.exe' successfully executes start-dev.ps1 script
- Whisper model configuration: Use "tiny" for testing/debugging, "large-v3-turbo" for production (configured in Backend/core/constants.py)
- Tiny model loads much faster than base/small models, ideal for development workflow

# lessons-learned-2025-09-06
- API endpoint paths must match exactly - use /process/* not /processing/*
- Authentication response field names vary - check actual response (token vs access_token)
- When a service method doesn't exist (like set_user_id), use the underlying service directly
- Routes can be registered but still return 404 if backend crashed - always check server health first
- Use check_routes.py script to verify all registered endpoints when debugging 404s
- Backend startup can be slow - wait and verify with health check before testing
- When testing workflow, run from Backend directory: cd Backend && cmd.exe /c "api_venv\Scripts\python.exe test_workflow.py"
- VocabularyPreloadService exists and works - no need to recreate it
- Always check both frontend console (browser MCP) AND backend logs when debugging connection issues