# Convenience wrapper to run a job with reuse enabled (keeps containers around)
param(
  [Parameter(Mandatory=$true)]
  [string] $JobId
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
& "$scriptDir\run-act-job.ps1" -JobId $JobId -Reuse
