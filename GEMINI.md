# DO NOT DELETE: This file is essential for project documentation.

# Global Development Standards & Memory

## Core Behavioral Rules

### Learning & Memory System

- **Failure Recovery**: Whenever you fail an action or tool use and later find out how to do it correctly, create a memory in this file that will make you never commit that mistake again
- **Solution Documentation**: Record proven solutions to recurring problems
- **Tool Optimization**: Document efficient tool usage patterns discovered

### Commit Standards

- **Never mention Claude in commits** - Use generic language for AI-generated content markers
- **Format**: `<type>: <description>` (imperative, lowercase, ≤50 chars)
- **Types**: feat, fix, docs, refactor, test, chore
- **Focus**: One logical change per commit
- **Body**: Explain "why" not "what" when needed

## Development Quality Standards

### Universal Clean Code Principles

- **Functions**: Keep < 20 lines, do one thing well, < 4 parameters
- **Names**: Intention-revealing, pronounceable, searchable
- **Comments**: Explain "why" not "what", remove dead code
- **Error Handling**: Use exceptions, handle at appropriate levels
- **Single Responsibility**: Classes and functions have one clear purpose
- **Code Hygiene**: Delete obsolete branches, commented-out blocks, or fallback implementations once they are no longer needed—source control is the safety net, not the live codebase. Never leave commented-out code; remove it entirely.
- **No Version Suffixes**: NEVER use version suffixes like \_v2, \_new, \_old, \_temp in file or class names. Source control exists for versioning. When replacing code, delete the old version completely. Names like models_v2.py, vocabulary_service_v2.py are unacceptable. Use clean, descriptive names without version indicators.
- **Fail Fast**: Avoid layering fallback code paths that silently paper over breakages; prefer failing early so the primary implementation is fixed rather than hidden
- **Purposeful Abstractions**: When multiple call sites share the same pattern, extract a helper or utility that enforces the desired behaviour (including fail-fast checks) so the logic is reusable and concise without reintroducing silent fallbacks

### Language-Specific Conventions

#### C# Standards

- **Naming**: PascalCase classes/methods, camelCase fields/variables
- **Async**: Always use async/await, suffix methods with "Async"
- **Nulls**: Use nullable reference types (`?`), null-coalescing (`??`, `?.`)
- **Resources**: Use `using` statements for disposables
- **Collections**: Prefer interfaces (IEnumerable, IList) in APIs

#### C++ Standards

- **Naming**: snake_case variables/functions, PascalCase classes
- **Memory**: Smart pointers (unique_ptr, shared_ptr), avoid raw pointers
- **Const**: Const correctness throughout
- **RAII**: Resource management via constructors/destructors
- **STL**: Prefer STL algorithms over manual loops

#### Python Standards

- **Naming**: snake_case everything except classes (PascalCase)
- **Types**: Use type hints for parameters and returns
- **Idioms**: List comprehensions, context managers, enumerate()
- **Docs**: Docstrings for all public functions/classes
- **F-strings**: Prefer over .format() or % formatting

#### React/TypeScript Standards

- **Components**: Function components with hooks
- **Props**: Define TypeScript interfaces for all props
- **State**: Appropriate hooks (useState, useEffect, useMemo)
- **Performance**: Memoize expensive calculations, prevent unnecessary re-renders
- **Files**: One component per file, descriptive names
- **Testing Discipline**: Use React Testing Library (or equivalent) helpers that wrap updates in `act`; when triggering state changes manually, wrap them in `await act(async () => { ... })` or await the RTL helpers so the test suite stays free of React “state update outside act()” warnings.

### Testing Requirements

- **Coverage Goals**: 60% minimum (acceptable), 80% target (commendable)
- **Testing Philosophy**: Test interfaces, not implementations
  - Focus on public APIs and user-facing behavior
  - Avoid testing implementation details
  - Tests should survive refactoring without changes
- **Independence**: Tests must be deterministic, isolated, and fast
  - Never treat 4xx/5xx/timeout responses as success; assertions must fail on unexpected status codes or error branches
  - Do not rely on global process state, seeded databases, or external services unless a dedicated fixture seeds and cleans them inside the test
  - Replace direct network/file/process access with fakes or dependency-injected stubs in unit tests
- **No Hidden Failures**: Never introduce `skip`, `xfail`, or similar tooling (e.g., `pytest.skip`, `pytest.mark.skip`, Jest's `test.skip`, Playwright's `test.fixme`) to bypass a failing path. Surface the failure and coordinate with the user if an explicit temporary skip is required; only the user decides when exceptions are appropriate.
- **Assertions**
  - Verify observable behavior and return values instead of mock call counts or private helpers
  - Fail if assertions depend on logging output or print statements
  - Ensure every test would fail on a real regression; counting DOM nodes, waiting for page loads, or checking generic truthy strings is not acceptable as the primary assertion
  - Assert the exact status code and contractually required payload; avoid "in {200, 422}"-style hedging
- **Contracts**
  - When an OpenAPI/JSON Schema exists, validate both requests and responses against it (locally or through an interceptor) so schema drift fails fast
  - Keep generated clients and schema definitions in sync with the source spec before landing feature work
- **Classification**
  - Long-running smoke checks (real browsers, external servers, CLI scripts) belong under a `manual` or `smoke` label and must be skipped by default in automated suites
  - Auto-generated code (_.gen.ts, generated/_, API clients) remains excluded from coverage targets
- **Structure**: Arrange-Act-Assert pattern with explicit arrange/act sections
- **Naming**: Descriptive descriptions covering scenario and expected outcome; defer to repository-specific conventions when they differ from these defaults
- **Security**: Never embed real credentials, bearer tokens, or host-specific secrets in tests or documentation—use fixtures or environment variables instead
- **Process Isolation**: Automated suites must not spawn external servers, browsers, or long-lived subprocesses; keep those flows in opt-in smoke/manual harnesses
- **Pyramid**: More unit tests, fewer integration/E2E tests, with clear differentiation between fast deterministic tests and optional smoke tests

### Pre-Test Creation Validation

- **Before writing any test**, ALWAYS ask yourself:
  1. "Does this test verify observable behavior, not implementation?"
  2. "Will this test survive refactoring without changes?"
  3. "Does this test fail meaningfully when the feature breaks?"
  4. "Am I testing the public contract, not internal mechanisms?"
  5. "Are there any hard-coded paths, credentials, or external dependencies?"
  6. "Am I using semantic selectors instead of array indices?"
- **Never create tests that**:
  - Count mock method calls instead of checking outcomes
  - Accept multiple status codes as valid (e.g., `status in {200, 500}`)
  - Test language features instead of business logic
  - Use brittle selectors (array indices, exact CSS values)
  - Pass with `assert True` or similar meaningless assertions
  - Silence failing behaviour via `skip`, `xfail`, `fixme`, `pending`, or any other opt-out markers without prior user approval
  - Hard-code absolute file paths or Windows-specific paths
  - Print results instead of asserting expected outcomes
  - Expose credentials, tokens, or sensitive data
  - Depend on external servers or real file systems without isolation
- **Dependency Discipline**: Favor upgrading dependencies and modernizing call sites over piling on shims; once migration paths are proven, remove legacy adapters entirely instead of keeping dual implementations

### Architecture Principles

- **Separation of Concerns**: Distinct features with minimal overlap
- **Modularity**: Independent development, testing, deployment
- **Scalability**: Design for horizontal scaling
- **Maintainability**: Simplicity over cleverness

## Claude Code Integration

### Slash Commands Usage

- **Always use analysis commands before making changes**:
  - `/codereview` → Analyze code quality and create improvement plan
  - `/patterns` → Review design patterns and create improvement plan
  - `/testing` → Analyze test coverage and create improvement plan
  - `/security` → Security analysis and create improvement plan
  - `/parallel` → Concurrency analysis and create improvement plan
  - `/architecture` → Architecture analysis and create improvement plan
  - `/comments` → Comment quality analysis and create improvement plan
  - `/documentation` → Documentation analysis and create improvement plan

### Subagent Utilization

- **Language experts are available**: python-expert, cpp-expert, csharp-expert, react-expert, plantuml-expert, latex-expert
- **Invoke proactively** when working with specific technologies
- **Leverage specialized knowledge** for language-specific best practices

### Workflow Pattern

1. **Analyze first** using appropriate slash commands
2. **Create improvement plan** with specific actionable tasks
3. **User reviews and customizes** the plan
4. **Execute plan** making actual code changes
5. **Document completion** and any problems encountered

### Enhanced Testing Workflow

1. **Analyze first** using `/testing` command when creating test suites
2. **Apply pre-flight checks** for every individual test before writing
3. **Create behavior-focused tests** that verify public contracts
4. **Review and validate** tests against quality guidelines
5. **Document any anti-patterns avoided** in commit messages

### E2E Test Best Practices

- **Semantic Selectors**: Prefer explicit instrumentation (`data-testid`, roles, accessible names) over array indices or structural heuristics
- **No Silent Fallbacks**: Avoid layered fallbacks (selectors, API shims, legacy branches) that keep tests green while the intended contract is broken—fail fast and fix the primary path or add the missing hook
- **Helper Functions Welcome**: If multiple tests need the same validation pattern, build shared helpers that still enforce fail-fast semantics; reducing duplication is good as long as the helper raises when the primary selector/instrumentation is missing
- **Error Handling**: Always check if element selection succeeded before interaction
- **Element Selection Pattern**:
  ```javascript
  // BAD: elements[0].click()
  // GOOD:
  const clicked = await page.evaluate(() => {
    const element = document.querySelector('[data-testid="submit-btn"]');
    if (element) {
      element.click();
      return true;
    }
    return false;
  });
  if (!clicked) throw new Error("Element not found");
  ```
- **Business Assertions**: Exercise full user workflows (authenticate, perform the action, verify persisted state or API response) and assert on domain-specific outcomes, not just navigation success or element existence
- **Dynamic URL Detection**: Never hard-code localhost URLs - use port detection
- **Shared Config**: Resolve all environment details through the canonical helpers for the project (e.g., `getFrontendUrl`, backend fixtures); never duplicate URLs, credentials, or ports inside tests or helpers
- **Browser Cleanup**: Always close pages and browsers in afterEach/afterAll hooks
- **Deterministic Waits**: Replace `setTimeout` sleeps with explicit waits on selectors, API responses, or other observable events so failures surface quickly
- **Data Lifecycle**: Seed and clean data through dedicated fixtures/helpers so tests stay isolated and idempotent; ad-hoc CLI seed scripts or manual cleanup is not acceptable for automated suites
- **Unified Harnesses**: Prefer real test runners (Jest, Playwright, pytest) or the repository's orchestrator over bespoke `node script.ts` flows so failures are reported and integrated with CI
- **Shared Tooling**: Reuse the project’s official helpers (e.g., orchestrators, test data managers, contract validators) instead of re-implementing setup/teardown logic in each suite

## Pre-Commit Validation Checklist

### Code Quality

- [ ] Functions are small and focused (< 20 lines)
- [ ] Names clearly express intent
- [ ] No commented-out code
- [ ] Error handling is appropriate
- [ ] Language conventions followed

### Testing & Documentation

- [ ] Tests cover new functionality
- [ ] Test coverage meets standards (80%+)
- [ ] Public APIs have documentation
- [ ] Complex logic is explained

### Commit Standards

- [ ] Commit message follows format
- [ ] Single logical change
- [ ] No sensitive data included
- [ ] No Claude mentions in commit

### Architecture & Security

- [ ] SOLID principles followed
- [ ] Security best practices applied
- [ ] Performance considerations addressed
- [ ] Dependencies properly managed

## Proven Solutions & Memories

### Common Tool Usage Patterns

- **Multiple file operations**: Use MultiEdit for batch changes to same file
- **Large codebases**: Use Task tool with specialized agents for complex searches
- **Analysis workflows**: Batch multiple tool calls for parallel execution
- **File searches**: Use Glob for patterns, Grep for content, Read for specific files

### Performance Optimizations

- **Batch tool calls**: Send multiple tool uses in single message when possible
- **Appropriate tools**: Use most specific tool for the task (don't use Bash for file reading)
- **Context management**: Use subagents to preserve main conversation context

### Error Prevention

- **File paths**: Always use absolute paths in file operations
- **Git operations**: Check git status before making assumptions about repository state
- **Dependencies**: Verify package/library availability before writing code that uses them
- **Testing**: Run tests and linting before considering work complete
- **WSL Testing**: Use PowerShell for npm/test commands to avoid bus errors and match Windows behavior
- **PowerShell Hook**: Automatic PowerShell wrapping for Python/pytest/npm commands is enabled via hook in `~/.claude/settings.json`
- **Legacy Cleanup**: After upgrading dependencies or finishing migrations, remove the superseded code paths immediately instead of keeping fallback branches or feature flags alive

### Cross-Platform Path Management

- **Never hard-code OS-specific paths**: Avoid `E:\Users\...` or `/home/user/...`
- **Use path.resolve() for project paths**: `path.resolve(__dirname, '..', 'Backend')` instead of hard-coded paths
- **Project root resolution**: Use `const projectRoot = path.resolve(__dirname, '..', '..')` pattern
- **Path joining**: Always use `path.resolve()` or `path.join()` instead of string concatenation
- **Test infrastructure**: All test orchestration must work cross-platform (Windows, Linux, macOS)

### Test Quality Failures to Avoid

- **Mock Call Counting Anti-Pattern**: Do not rely on `assert_session_operations` (or similar helpers) as the primary assertion—prefer observable return values/state changes and reserve these helpers for critical side-effects that cannot be observed otherwise
- **Status Code Tolerance Anti-Pattern**: Never write `assert status_code in {200, 500}`—always assert the specific expected outcome
- **Array Index Selector Anti-Pattern**: Never use `buttons[1]` or `elements[0].click()` in E2E tests - use semantic selectors like role queries, data-testid, or semantic CSS selectors
- **Trivial Test Anti-Pattern**: Never test Python language features or empty implementations - only test business logic
- **Implementation Coupling Anti-Pattern**: Never test private methods or internal structure - focus on public contracts and observable behavior
  -- **Hard-coded Path Anti-Pattern**: Never use absolute Windows paths like `E:\Users\...` - use relative paths with `path.resolve(__dirname, '..', 'Backend')`
- **Manual Script Anti-Pattern**: Never create scripts that print results and require manual interpretation - convert to proper unit tests with assertions
- **Credential Exposure Anti-Pattern**: Never hard-code bearer tokens, passwords, or API keys in test files - use test helpers and environment variables
- **External Dependency Anti-Pattern**: Never write tests that depend on real file systems, external servers, or seeded databases without proper test isolation
- **Filesystem Coupling Anti-Pattern**: Never test against real directories like `assert Path('/real/path').exists()` - use dependency injection and mock filesystems

### Integration Testing Anti-Patterns (Core Violations)

- **Configuration Masquerading as Integration Anti-Pattern**: NEVER create "integration" tests that only verify object creation, configuration mapping, or factory instantiation - integration tests must exercise the actual integration between real components performing real work
- **Missing Integration Verification Anti-Pattern**: If a test doesn't verify that components actually work together to produce the expected outcome, it's not an integration test - it's a unit test disguised with an integration label
- **Shallow Integration Anti-Pattern**: Tests that call `service.create()` and `assert service is not None` without exercising the service's core functionality are testing object instantiation, not integration

### AI/ML Service Integration Testing Anti-Patterns (Specific Examples)

- **Factory Bypass Anti-Pattern**: NEVER remove environment variable testing in favor of direct factory calls like `get_service("model-name")` when the intent is to test environment-based configuration - test the full environment→factory→service→functionality chain
- **Model Mismatch Testing Anti-Pattern**: When testing environment configuration like `LANGPLUG_TRANSCRIPTION_SERVICE=whisper-tiny`, test that the environment variable actually changes behavior, don't bypass it with hardcoded factory parameters

### AI Service Testing Best Practices

- **Minimal Functional Tests**: AI service "hello world" tests should be < 10 lines, < 10 seconds, use smallest models, and actually perform the core operation with real input/output validation
- **Graceful Dependency Skipping**: Use `pytest.skip()` when optional AI dependencies (like NeMo) aren't installed rather than failing tests
- **Environment-Specific Models**: Test environment should use fastest/smallest model variants (whisper-tiny, opus-de-es, nllb-distilled-600m) while production uses larger models

### PowerShell Hook Configuration

- **Automatic Command Wrapping**: Hook automatically wraps Python/pytest/npm/node/npx commands with `powershell.exe`
- **Hook Location**: `~/.claude/hooks/powershell_wrapper.py`
- **Configuration**: Registered in `~/.claude/settings.json` as PreToolUse hook for Bash tool
- **Commands Wrapped**: `python`, `python3`, `pytest`, `npm`, `node`, `npx`
- **Benefits**: Ensures Windows behavior in WSL, avoids bus errors, matches expected encoding/environment

---

**Remember**: This file should evolve with lessons learned. Add new memories and solutions as they're discovered to prevent repeating mistakes and improve development quality.

- Always run the servers with powershell to have the windows setting instead of WSL
- **NEVER use emojis or Unicode characters in Python code** - Windows PowerShell has encoding issues with Unicode characters (🚀, 📊, ✅, ❌, etc.). Always use plain ASCII text like [INFO], [ERROR], [WARN], [GOOD], [POOR] instead
- **ALWAYS activate Backend venv before Python/pytest commands** - Use the venv path: `/mnt/c/Users/Jonandrop/IdeaProjects/LangPlug/Backend/api_venv/Scripts/activate && python -m pytest ...`
- **NO VERSION SUFFIXES IN CODE**: NEVER use \_v2, \_new, \_old, \_temp, \_backup suffixes in filenames or class names. Source control (Git) handles versioning. When replacing code, delete the old version completely. If you need to reference old code, use git history.

## PowerShell Integration Hook (Last Resort)

A PreToolUse hook is configured in `~/.claude/settings.json` that automatically intercepts Python/Node commands and suggests PowerShell-wrapped versions. This hook should be a **last resort** when Claude consistently forgets to use PowerShell commands.

**Preferred approach**: Explicitly request PowerShell commands in prompts
**Hook approach**: Automatic interception and guidance (already configured)

The hook intercepts: `python`, `python3`, `pytest`, `pip`, `npm`, `node`, `npx`
Location: `~/.claude/hooks/powershell_wrapper.py`

## Backend Virtual Environment

**Critical**: All Backend Python/pytest commands MUST use the virtual environment:

- Path: `/mnt/c/Users/Jonandrop/IdeaProjects/LangPlug/Backend/api_venv/Scripts/activate`
- Command pattern: `cd /mnt/c/Users/Jonandrop/IdeaProjects/LangPlug/Backend && powershell.exe -Command ". api_venv/Scripts/activate; python -m pytest ..."
- This ensures all dependencies are available and tests run in the correct environment

---

**Protected Files**

The following files are considered essential and should not be deleted:

- `AGENTS.md`
- `QWEN.MD.md`
- `GEMINI.md`
- `CLAUDE.md`
