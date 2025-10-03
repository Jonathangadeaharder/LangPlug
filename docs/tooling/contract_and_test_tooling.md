# Contract and Test Tooling

These tools enforce the CDD and TDD policies. Keep installations up to date and integrate them into
your workflows.

**Note**: This document has been updated to reference the new unified cross-platform scripts. See `docs/TESTING_STRATEGY.md` for comprehensive guidance.

## Contract Authoring

- **OpenAPI export and client generation**: Use the unified cross-platform script that handles both OpenAPI export and TypeScript client generation.

  ```bash
  # Cross-platform unified script (recommended)
  python scripts/generate_typescript_client.py
  ```

  **Legacy alternatives** (deprecated, will be removed):

  ```bash
  # Manual OpenAPI export (if needed)
  cd Backend
  python export_openapi.py --output ../openapi_spec.json

  # Manual client generation (if needed)
  cd Frontend
  npm run generate-client
  ```

- **Schema validation (Zod/Datamodel code)**: Frontend schemas live under `Frontend/src/utils/`. Use
  the generated types to keep schemas aligned with contracts.

## Contract Testing

- **Professional test management**: Use the new test management script for comprehensive testing.

  ```bash
  # Run all tests with professional reporting
  python scripts/test_management.py

  # Run contract tests specifically
  python scripts/test_management.py --category contract

  # Run failed tests only
  python scripts/test_management.py --failed-only
  ```

- **Backend contract tests**: Located under `Backend/tests/` (marked with `@pytest.mark.contract`).

  ```bash
  cd Backend
  python -m pytest -m contract
  ```

- **Frontend contract suites**: See `Frontend/src/test/contract/`.
  ```bash
  cd Frontend
  npm run test
  ```
- **Integration smoke tests**: Run full stack verification for high-impact changes.
  ```bash
  cd Backend
  python simulate_ci.py --stage contract
  ```

## Protective Testing

- **Backend standard suite**:

  ```bash
  cd Backend
  pytest
  pytest --cov=core --cov=api --cov=services
  ```

  For maximum stability, prefer Postgres-backed runs:

  ```bash
  cd Backend
  docker compose -f docker-compose.postgresql.yml up -d db
  USE_TEST_POSTGRES=1 TEST_POSTGRES_URL="postgresql+asyncpg://langplug_user:langplug_password@localhost:5432/langplug" pytest
  ```

- **Convenience scripts**:

  ```bash
  # Linux/macOS
  cd Backend && ./scripts/run_tests_postgres.sh

  # Windows PowerShell
  cd Backend; ./scripts/run_tests_postgres.ps1
  ```

- **Frontend behavioral tests**:
  ```bash
  cd Frontend
  npm run test
  ```
- **Linting**:
  ```bash
  cd Backend && ruff check .
  cd Frontend && npm run lint
  ```

## Automation Hooks

- **Pre-commit (optional)**: Install `pre-commit` and use the config in `.pre-commit-config.yaml` when
  available to catch lint/format issues before pushing.
- **CI parity**: Mirror CI commands locally. If CI introduces new contract gates, update this file and
  the checklist immediately.

## Troubleshooting

- If contract tests fail because of stale clients, regenerate the OpenAPI client and re-run the suite.
- When backend schemas change, re-export the spec and update Pydantic models. Keep migrations synced.
- For frontend schema mismatches, run `npm run build-types` (if defined) to refresh generated types.

Keep this document updated as tooling evolves. Submit a doc update in the same PR whenever you add or
modify contract/test tooling.
