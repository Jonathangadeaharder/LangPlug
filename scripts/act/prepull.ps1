# Pull common images used by workflows so act won't re-download them each run
param(
  [string[]] $Images = @('catthehacker/ubuntu:full-latest','postgres:15')
)

# Check if docker is available
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
  Write-Error "Docker CLI not found. Please install Docker Desktop and ensure 'docker' is in PATH."
  exit 1
}

foreach ($img in $Images) {
  Write-Host "Pulling $img..."
  docker pull $img
  if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to pull $img"
    exit 1
  }
}

Write-Host "Done. Images pulled."
