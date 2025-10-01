---
description: E2E test best practices and patterns
auto_execution_mode: 3
---

## Workflow
- **Name**: e2e-test-best-practices
- **Description**: E2E test best practices and patterns

## Steps
- None

## Best Practices
- **Selectors**
  - **semantic_selectors**: Prefer explicit instrumentation (data-testid, roles, accessible names) over array indices or structural heuristics
  - **no_silent_fallbacks**: Avoid layered fallbacks (selectors, API shims, legacy branches) that keep tests green while the intended contract is broken—fail fast and fix the primary path or add the missing hook
  - **helper_functions**: If multiple tests need the same validation pattern, build shared helpers that still enforce fail-fast semantics; reducing duplication is good as long as the helper raises when the primary selector/instrumentation is missing
  - **error_handling**: Always check if element selection succeeded before interaction
- **Element Selection Pattern**
  - **bad**: `elements[0].click()`
  - **good**: `const clicked = await page.evaluate(() => { const element = document.querySelector('[data-testid="submit-btn"]'); if (element) { element.click(); return true; } return false; }); if (!clicked) throw new Error('Element not found');`
- **Business Assertions**: Exercise full user workflows (authenticate, perform the action, verify persisted state or API response) and assert on domain-specific outcomes, not just navigation success or element existence
- **Dynamic URL Detection**: Never hard-code localhost URLs - use port detection
- **Shared Config**: Resolve all environment details through the canonical helpers for the project (e.g., getFrontendUrl, backend fixtures); never duplicate URLs, credentials, or ports inside tests or helpers
- **Browser Cleanup**: Always close pages and browsers in afterEach/afterAll hooks
- **Deterministic Waits**: Replace setTimeout sleeps with explicit waits on selectors, API responses, or other observable events so failures surface quickly
- **Data Lifecycle**: Seed and clean data through dedicated fixtures/helpers so tests stay isolated and idempotent; ad-hoc CLI seed scripts or manual cleanup is not acceptable for automated suites
- **Unified Harnesses**: Prefer real test runners (Jest, Playwright, pytest) or the repository's orchestrator over bespoke node script.ts flows so failures are reported and integrated with CI
- **Shared Tooling**: Reuse the project's official helpers (e.g., orchestrators, test data managers, contract validators) instead of re-implementing setup/teardown logic in each suite

## Requirements
- Semantic Selectors: Prefer explicit instrumentation (data-testid, roles, accessible names) over array indices or structural heuristics
- No Silent Fallbacks: Avoid layered fallbacks (selectors, API shims, legacy branches) that keep tests green while the intended contract is broken—fail fast and fix the primary path or add the missing hook
- Helper Functions Welcome: If multiple tests need the same validation pattern, build shared helpers that still enforce fail-fast semantics
- Error Handling: Always check if element selection succeeded before interaction
- Business Assertions: Exercise full user workflows and assert on domain-specific outcomes
- Dynamic URL Detection: Never hard-code localhost URLs - use port detection
- Shared Config: Resolve all environment details through canonical helpers
- Browser Cleanup: Always close pages and browsers in afterEach/afterAll hooks
- Deterministic Waits: Replace setTimeout sleeps with explicit waits
- Data Lifecycle: Seed and clean data through dedicated fixtures/helpers
- Unified Harnesses: Prefer real test runners over bespoke scripts
- Shared Tooling: Reuse the project's official helpers
