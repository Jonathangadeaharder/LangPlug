---
description: Analyze test coverage and create improvement plan
auto_execution_mode: 3
---

## Workflow
- **Name**: testing
- **Description**: Analyze test coverage and create improvement plan

## Steps
1. **Type**: analyze
   - **analysis_type**: test_coverage
   - **description**: Analyze test coverage and create improvement plan
2. **Type**: plan
   - **description**: Create specific actionable tasks for testing improvements

## Triggers
- /testing

## Requirements
- Always use analysis commands before making changes
- Create improvement plan with specific actionable tasks
- User reviews and customizes the plan
- Execute plan making actual code changes
- Document completion and any problems encountered
- Apply pre-flight checks for every individual test before writing
- Create behavior-focused tests that verify public contracts
- Review and validate tests against quality guidelines
- Document any anti-patterns avoided in commit messages
