Scripts to make working with `act` easier on Windows PowerShell.

prepull.ps1

- Pulls common images used by the workflows so `act` doesn't need to download them repeatedly.

run-act-job.ps1 -JobId <job-id> [-Reuse] [-DryRun]

- Runs a single job with `--pull=false` by default.
- Use `-Reuse` to keep containers between runs for faster iterations.
- Use `-DryRun` to validate workflow without creating containers.

run-with-reuse.ps1 -JobId <job-id>

- Shortcut to run a job with `-Reuse` enabled.

Examples:

```powershell
# Pre-pull images once
.\scripts\act\prepull.ps1

# Run the backend contract tests job without pulling
.\scripts\act\run-act-job.ps1 -JobId backend-contract-tests

# Run and keep containers around
.\scripts\act\run-with-reuse.ps1 -JobId backend-contract-tests

# Dry run
.\scripts\act\run-act-job.ps1 -JobId backend-contract-tests -DryRun
```

Notes:

- Ensure Docker Desktop is installed and running, and `docker` is available on PATH.
- These scripts are intentionally simple and PowerShell-native so they work on Windows hosts.
