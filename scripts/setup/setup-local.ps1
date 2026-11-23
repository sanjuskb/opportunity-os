# Setup script for Windows developers
Write-Host "Setting up Opportunity OS local development environment..." -ForegroundColor Cyan

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Created .env from .env.example" -ForegroundColor Green
}

Write-Host "Installing Node.js monorepo dependencies..." -ForegroundColor Cyan
pnpm install

Write-Host "Syncing Python backend dependencies..." -ForegroundColor Cyan
Push-Location apps/api
uv sync
Pop-Location

Write-Host "`nSetup complete! You can start developing with 'make dev' or pnpm dev." -ForegroundColor Green
