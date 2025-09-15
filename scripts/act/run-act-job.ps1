<#
Run a specific act job without pulling images every time.
Usage:
  .\run-act-job.ps1 -JobId backend-contract-tests
  .\run-act-job.ps1 -JobId backend-contract-tests -Reuse
#>
param(
  [Parameter(Mandatory=$true)]
  [string] $JobId,
  [switch] $Reuse,
  [switch] $DryRun = $false
)

$baseArgs = @('-j', $JobId, '--pull=false')
if ($Reuse) { $baseArgs += '--reuse' }
if ($DryRun) { $baseArgs += '--dryrun' }

Write-Host "Running: act $($baseArgs -join ' ')"
act @baseArgs

if ($LASTEXITCODE -ne 0) { throw "act exited with code $LASTEXITCODE" }
