---
description: React language expert for specialized React development tasks
auto_execution_mode: 3
---

## Workflow
- **Name**: react-expert
- **Description**: React language expert for specialized React development tasks

## Steps
1. **Type**: specialist
   - **language**: react
   - **description**: Invoke proactively when working with React technologies
2. **Type**: apply
   - **description**: Leverage specialized knowledge for React-specific best practices

## Triggers
- react-expert

## Requirements
- Language experts are available: python-expert, cpp-expert, csharp-expert, react-expert, plantuml-expert, latex-expert
- Invoke proactively when working with specific technologies
- Leverage specialized knowledge for language-specific best practices
- Keep changes minimal and focused; do not refactor unrelated code
- Follow existing naming and structure; no one-letter variables
- Avoid inline comments unless necessary for clarity

## Standards
- **components**: Function components with hooks
- **props**: Define TypeScript interfaces for all props
- **state**: Appropriate hooks (useState, useEffect, useMemo)
- **performance**: Memoize expensive calculations, prevent unnecessary re-renders
- **files**: One component per file, descriptive names
- **testing**: Use React Testing Library (or equivalent) helpers that wrap updates in act; when triggering state changes manually, wrap them in await act(async () => { ... }) or await the RTL helpers so the test suite stays free of React 'state update outside act()' warnings
