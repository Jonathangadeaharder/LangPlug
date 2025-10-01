---
description: Standard workflow pattern for development tasks
auto_execution_mode: 3
---

## Workflow
- **Name**: workflow-pattern
- **Description**: Standard workflow pattern for development tasks

## Steps
1. **Type**: analyze
   - **step**: 1
   - **description**: Analyze first using appropriate slash commands
   - **commands**: /codereview, /patterns, /testing, /security, /parallel, /architecture, /comments, /documentation
2. **Type**: plan
   - **step**: 2
   - **description**: Create improvement plan with specific actionable tasks
3. **Type**: review
   - **step**: 3
   - **description**: User reviews and customizes the plan
4. **Type**: execute
   - **step**: 4
   - **description**: Execute plan making actual code changes
5. **Type**: document
   - **step**: 5
   - **description**: Document completion and any problems encountered

## Requirements
- Analyze first using appropriate slash commands
- Create improvement plan with specific actionable tasks
- User reviews and customizes the plan
- Execute plan making actual code changes
- Document completion and any problems encountered
- For large changes, propose a short stepwise plan; update as you progress
- Validate with targeted pytest runs in the venv; then broader suite
