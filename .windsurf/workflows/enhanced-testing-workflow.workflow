---
description: Enhanced testing workflow for creating test suites
auto_execution_mode: 3
---

## Workflow
- **Name**: enhanced-testing-workflow
- **Description**: Enhanced testing workflow for creating test suites

## Steps
1. **Type**: analyze
   - **step**: 1
   - **description**: Analyze first using /testing command when creating test suites
   - **command**: /testing
2. **Type**: validate
   - **step**: 2
   - **description**: Apply pre-flight checks for every individual test before writing
   - **checks**: Does this test verify observable behavior, not implementation?; Will this test survive refactoring without changes?; Does this test fail meaningfully when the feature breaks?; Am I testing the public contract, not internal mechanisms?; Are there any hard-coded paths, credentials, or external dependencies?; Am I using semantic selectors instead of array indices?
3. **Type**: create
   - **step**: 3
   - **description**: Create behavior-focused tests that verify public contracts
4. **Type**: review
   - **step**: 4
   - **description**: Review and validate tests against quality guidelines
5. **Type**: document
   - **step**: 5
   - **description**: Document any anti-patterns avoided in commit messages

## Requirements
- Analyze first using /testing command when creating test suites
- Apply pre-flight checks for every individual test before writing
- Create behavior-focused tests that verify public contracts
- Review and validate tests against quality guidelines
- Document any anti-patterns avoided in commit messages
- Never create tests that count mock method calls instead of checking outcomes
- Never create tests that accept multiple status codes as valid
- Never create tests that test language features instead of business logic
- Never create tests that use brittle selectors (array indices, exact CSS values)
- Never create tests that pass with assert True or similar meaningless assertions
- Never create tests that silence failing behaviour via skip, xfail, fixme, pending
- Never create tests that hard-code absolute file paths or Windows-specific paths
- Never create tests that print results instead of asserting expected outcomes
- Never create tests that expose credentials, tokens, or sensitive data
- Never create tests that depend on external servers or real file systems without isolation
