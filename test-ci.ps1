$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendResults = Join-Path $projectRoot "backend\test-results"
$frontendResults = Join-Path $projectRoot "frontend\test-results"

New-Item -ItemType Directory -Force -Path $backendResults, $frontendResults | Out-Null

Write-Host "Running backend CI tests..."
Push-Location (Join-Path $projectRoot "backend")
try {
    & ".\venv\Scripts\python.exe" -m pytest --junitxml="test-results\junit.xml"
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}
finally {
    Pop-Location
}

Write-Host "Running frontend CI checks..."
Push-Location (Join-Path $projectRoot "frontend")
try {
    npm run ci
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}
finally {
    Pop-Location
}

Write-Host "CI checks passed. JUnit files are under backend/test-results and frontend/test-results."
