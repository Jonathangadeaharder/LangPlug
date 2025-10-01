# Frontend Code Quality Tools

This document describes the code quality tools configured for the React/TypeScript frontend.

## Tools Overview

### 1. ESLint

**Purpose**: Lints JavaScript/TypeScript code, enforces React best practices and accessibility

**Key Features**:

- TypeScript error detection
- React-specific rules (hooks, component patterns)
- Accessibility checks (jsx-a11y)
- Auto-fixable issues

**Configuration**: `eslint.config.js`

**Usage**:

```bash
npm run lint              # Check for issues
npm run lint:fix          # Auto-fix issues
```

### 2. Prettier

**Purpose**: Enforces consistent code formatting

**Key Features**:

- Automatic code formatting
- Consistent style across team
- Integrates with ESLint

**Configuration**: `.prettierrc`

**Usage**:

```bash
npm run format            # Format all files
npm run format:check      # Check formatting without changes
```

### 3. TypeScript

**Purpose**: Static type checking for type safety

**Key Features**:

- Strict type checking enabled
- Catch errors at compile time
- Better IDE support

**Configuration**: `tsconfig.json`

**Usage**:

```bash
npm run typecheck         # Type check without emitting
npm run build             # Type check + build
```

### 4. Stylelint

**Purpose**: Lints CSS-in-JS (styled-components)

**Key Features**:

- CSS best practices
- styled-components support
- Auto-fixable CSS issues

**Configuration**: `.stylelintrc.json`

**Usage**:

```bash
npm run style             # Check styles
npm run style:fix         # Auto-fix style issues
```

### 5. Semgrep

**Purpose**: Security and pattern analysis

**Key Features**:

- Security vulnerability detection
- Custom rule support
- OWASP pattern matching

**Configuration**: `.semgrep.yml`

**Usage**:

```bash
# Run from project root
semgrep --config Frontend/.semgrep.yml Frontend/src
```

### 6. Vitest

**Purpose**: Unit and integration testing

**Key Features**:

- Fast test execution
- Coverage reporting
- Mock support

**Configuration**: `vitest.config.ts`

**Usage**:

```bash
npm test                  # Run all tests
npm run test:watch        # Watch mode
npm run coverage          # Generate coverage report
```

## Code Metrics

### 7. Code Complexity Analysis

**Purpose**: Measure code complexity and maintainability

**Tools**: Lizard, ESLint complexity plugin

**Usage**:

```bash
npm run metrics               # Comprehensive metrics report
npm run metrics:complexity    # Complexity analysis
npm run metrics:duplication   # Find duplicate code
npm run metrics:type-coverage # TypeScript coverage
```

**Metrics Tracked**:

- Cyclomatic complexity
- Cognitive complexity
- Lines of code per function
- Code duplication percentage
- TypeScript type coverage

**Target Values**:

- Cyclomatic complexity: < 10
- Function length: < 50 lines
- Code duplication: < 5%
- TypeScript coverage: > 90%

## Combined Workflows

### Quick Quality Check

```bash
npm run quality
```

Runs: lint, format check, style check, and type check

### Fix All Auto-fixable Issues

```bash
npm run quality:fix
```

Runs: lint fix, format, and style fix

### Full Pre-commit Check

```bash
npm run quality && npm test
```

### Comprehensive Metrics Report

```bash
npm run metrics
```

Generates report with all code quality metrics

## IDE Integration

### VS Code

Install extensions:

- ESLint (`dbaeumer.vscode-eslint`)
- Prettier (`esbenp.prettier-vscode`)
- Stylelint (`stylelint.vscode-stylelint`)

Add to `.vscode/settings.json`:

```json
{
  "editor.formatOnSave": true,
  "editor.defaultFormatter": "esbenp.prettier-vscode",
  "editor.codeActionsOnSave": {
    "source.fixAll.eslint": true,
    "source.fixAll.stylelint": true
  },
  "eslint.validate": [
    "javascript",
    "javascriptreact",
    "typescript",
    "typescriptreact"
  ]
}
```

## CI/CD Integration

Add to CI pipeline:

```yaml
- name: Quality Checks
  run: |
    cd Frontend
    npm run quality
    npm test
```

## Common Issues and Fixes

### ESLint: "Parsing error"

- Ensure `@typescript-eslint/parser` is installed
- Check that `parserOptions` in eslint.config.js is correct

### Prettier conflicts with ESLint

- Make sure `eslint-config-prettier` is last in extends array
- This is already configured correctly

### Stylelint: "Unknown rule"

- Update stylelint and plugins: `npm update stylelint`
- Check `.stylelintrc.json` for deprecated rules

### TypeScript: "Cannot find module"

- Run `npm install`
- Check `tsconfig.json` paths configuration

## Quality Standards

### Minimum Requirements

- **ESLint**: 0 errors, 0 warnings (enforced by `--max-warnings 0`)
- **Prettier**: All files formatted
- **TypeScript**: No type errors
- **Test Coverage**: 80%+ for critical components

### Best Practices

1. Run `npm run quality:fix` before committing
2. Fix accessibility warnings (jsx-a11y)
3. Avoid `any` types - use proper TypeScript types
4. Write tests for new components/hooks
5. Use semantic HTML and ARIA labels

## Security Checks

Semgrep rules check for:

- XSS vulnerabilities (dangerouslySetInnerHTML)
- Hardcoded credentials
- Sensitive data in localStorage
- Use of eval()
- console.log() in production code

## Troubleshooting

### "Module not found" errors

```bash
rm -rf node_modules package-lock.json
npm install
```

### Pre-commit hooks not running

```bash
npx husky install
```

### Slow linting

- Add more patterns to `.eslintignore`
- Use `--cache` flag: `eslint --cache src`

## Additional Resources

- [ESLint Rules](https://eslint.org/docs/rules/)
- [Prettier Options](https://prettier.io/docs/en/options.html)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/intro.html)
- [React Testing Library](https://testing-library.com/docs/react-testing-library/intro/)
- [Semgrep Rules](https://semgrep.dev/r)
- [jsx-a11y Rules](https://github.com/jsx-eslint/eslint-plugin-jsx-a11y)
