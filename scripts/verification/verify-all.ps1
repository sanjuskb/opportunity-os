# PowerShell script to verify all local checks
Write-Host "Running Opportunity OS Full Verification..." -ForegroundColor Cyan

Write-Host "`n1. Running pnpm Type Check..." -ForegroundColor Yellow
pnpm type-check

Write-Host "`n2. Running pnpm Tests..." -ForegroundColor Yellow
pnpm test

Write-Host "`n3. Running Python tests in apps/api..." -ForegroundColor Yellow
Push-Location apps/api
uv run pytest
uv run ruff check .
Pop-Location

Write-Host "`nAll verification checks executed successfully!" -ForegroundColor Green
