# Contributing to LangPlug

This guide converts the CDD and TDD rule files into concrete expectations for day-to-day
engineering. Every change must respect both contract-driven development (CDD) and the 80/20
protective test philosophy.

## Prerequisites

- Install backend dependencies with the documented virtualenv (`Backend/requirements-dev.txt`).
- Install frontend dependencies via `npm install` in `Frontend/`.
- Install tooling required for linting, testing, and contract validation:
  - Python: `pytest`, `pytest-asyncio`, `pytest-cov`, `ruff`, `mypy` (optional for local type checks).
  - Node: `npm run lint`, `npm run test`, `npm run test-contract` (see tooling doc for scripts).
  - Contract tooling: `generate-ts-client` script for OpenAPI client generation, `openapi-spec` export
    helpers in `Backend/scripts/`.
- Ensure you can run the backend using `python run_backend.py` (Windows users must use the
  PowerShell wrapper shown in the development guide).

## Core Workflow

1. **Start With a Contract**
   - Create or update the shared API contract (OpenAPI spec, schema modules, or gRPC proto) before any
     implementation.
   - Stub consumer/provider clients from the contract (`generate-ts-client.sh` or language-specific
     generators).
   - Get contract changes reviewed and versioned (see "Contract Lifecycle").
2. **Design With Guarantees**
   - Document how the component satisfies existing contracts, including preconditions and guarantees.
   - Update service-level docs in `docs/` or feature-specific READMEs with the new contract behavior.
3. **Write Protective Tests First**
   - Author tests that capture the agreed behavior prior to implementation. Follow the 80/20 guidance:
     one happy path, one invalid input defense, and one critical boundary variant unless the feature
     requires more coverage.
   - Prefer interface-level tests that exercise the module through HTTP, public service functions, or
     command handlers.
4. **Implement and Validate**
   - Implement the feature while keeping code aligned with the contract and tests. Update docs and
     changelogs as you go.
   - Run the full validation suite (lint, unit, contract tests) locally before opening a pull request.

## Contract Lifecycle Requirements

- **Definition**: Contracts live beside their owning service (`Backend/api/openapi_spec.py`, frontend
  schema modules, etc.). Every change must include documentation that explains the new behavior.
- **Review**: All contract updates require peer review. Highlight impacted consumers and expected
  migration steps in the pull request description.
- **Versioning**: Apply semantic versioning to contracts. Increment:
  - PATCH for compatible additions or documentation updates.
  - MINOR for additive changes that require new consumer support.
  - MAJOR for breaking changes. Breaking updates must include shims or a sunset plan.
- **Automation**: Update and run contract tests (`pytest -k contract`, frontend contract suites) on
  every change. CI build must fail if contracts drift from generated clients or schema validators.
- **Communication**: Notify connected teams when contracts change. Include release notes and upgrade
  paths in `docs/` and the PR body.

## Protective Testing Expectations (80/20)

- Keep tests behavior-focused. Avoid asserting internal implementation details, private attributes,
  or call counts.
- Tests must read like specifications. Use descriptive names (e.g., `test_register_returns_token`).
- Provide minimal setup. Use shared fixtures (`AuthTestHelper`, `url_builder`) instead of duplicating
  boilerplate.
- Default coverage template per feature:
  - Happy path scenario proving the contract works end-to-end.
  - Invalid or missing input scenario that should fail gracefully.
  - Single high-risk boundary (size limit, state transition) that protects against regressions.
- Document any additional scenarios beyond the template in the test module docstring so reviewers know
  why extra coverage exists.

## Pull Request Expectations

- Update relevant documentation (`docs/`, feature guides, API references) alongside code changes.
- Run and attach results for:
  - `cd Backend && pytest`
  - `cd Backend && pytest --cov=core --cov=api --cov=services` for coverage-sensitive work
  - Note: Each test must complete within 60 seconds. The backend enforces a global timeout via `pytest-timeout` (see `Backend/pytest.ini`). If you need to run in constrained environments (e.g., seccomp-restricted sandboxes), set `SKIP_DB_HEAVY_TESTS=1` to skip DB-heavy perf/security specs while iterating:
    - `cd Backend && SKIP_DB_HEAVY_TESTS=1 pytest tests/performance tests/security`
  - `cd Backend && ruff check .`
  - `cd Frontend && npm run test` and `npm run test-contract` when frontend contracts are impacted
- Confirm generated artifacts are up to date (OpenAPI client, typed schemas, alembic migrations).
- Complete the review checklists in `docs/review_checklists.md` before requesting review.

## Filing and Reviewing Changes

- Use draft pull requests to share WIP contract proposals early. Mark sections that still need
  approvals from stakeholders.
- Keep commits scoped: one contract update per commit where possible, followed by implementation and
  test commits.
- During review, respond to checklist items and link to contract approvals (issue, thread, or meeting
  notes).

## Testing Notes and Pitfalls

- Prefer in-process HTTP tests using `httpx.AsyncClient` with `ASGITransport(app=create_app())`.
- For DB-backed API tests, rely on the `async_client` and `db_session` fixtures in `Backend/tests/conftest.py` which:
  - Use a single, file-backed SQLite database per run to avoid in-memory/StaticPool deadlocks.
  - Unify the app-level engine and test engine by exporting `LANGPLUG_DATABASE_URL` to the same sqlite file.
  - Provide a clean schema per test via create/drop cycles.
- If your environment has restricted syscalls, prefer `pytest.mark.asyncio` in new async tests rather than AnyIO’s trio mode.

## Support

If you are unsure how to apply the policies, open a discussion in the project's communication channel
or tag the platform maintainers. When in doubt, pause implementation until the contract is approved
and protective tests are in place.
