
# Improved Project Structure

This document proposes a new, cleaner project structure that follows best practices for separation of concerns and low mental complexity.

```
/
├── .github/
│   └── workflows/
│       ├── code-quality.yml
│       ├── contract-tests.yml
│       ├── create-release.yml
│       ├── deploy-frontend.yml
│       ├── deploy.yml
│       ├── docs-check.yml
│       ├── e2e-tests.yml
│       ├── fast-tests.yml
│       ├── README.md
│       ├── security-scan.yml
│       ├── status-dashboard.yml
│       ├── tests-nightly.yml
│       ├── tests.yml
│       └── unit-tests.yml
├── .vscode/
├── config/
│   ├── nginx/
│   │   └── nginx.conf
│   ├── .env.example
│   ├── .env.production
│   └── .secrets.baseline
├── docs/
│   ├── architecture/
│   ├── assets/
│   └── guide/
├── logs/
│   ├── backend/
│   │   └── app.log
│   └── frontend/
│       └── app.log
├── packages/
│   ├── backend/
│   │   ├── src/
│   │   │   ├── api/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── deps.py
│   │   │   │   ├── endpoints/
│   │   │   │   └── security.py
│   │   │   ├── core/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── config.py
│   │   │   │   └── utils.py
│   │   │   ├── data/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── models/
│   │   │   │   └── services/
│   │   │   ├── main.py
│   │   │   └── __init__.py
│   │   ├── tests/
│   │   │   ├── integration/
│   │   │   ├── unit/
│   │   │   └── conftest.py
│   │   ├── .env
│   │   ├── poetry.lock
│   │   └── pyproject.toml
│   └── frontend/
│       ├── src/
│       │   ├── app/
│       │   │   ├── components/
│       │   │   ├── routes/
│       │   │   ├── services/
│       │   │   └── styles/
│       │   ├── main.tsx
│       │   └── index.html
│       ├── tests/
│       │   ├── e2e/
│       │   ├── integration/
│       │   └── unit/
│       ├── package.json
│       ├── tsconfig.json
│       └── vite.config.ts
├── scripts/
│   ├── deploy.sh
│   └── test.sh
├── tools/
│   ├── get_coverage.py
│   └── lint.sh
├── .gitignore
├── README.md
```
