param(
  [string]$RepoPath = (Resolve-Path '..').Path
)

Write-Host "Setting up git repository in: $RepoPath" -ForegroundColor Cyan
try {
  if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host 'Git is not installed or not in PATH. Please install Git and rerun.' -ForegroundColor Yellow
    exit 1
  }
} catch {
  Write-Host 'Unable to check for git. Ensure Git is installed.' -ForegroundColor Yellow
}

Push-Location $RepoPath
git init

# Commit 1: module
git add src/*.psm1 src/*.psd1
git commit -m "feat(module): add VNPCfix modular PowerShell module with core, UI, security, diagnostics, and repairs"

# Commit 2: entrypoint
git add PCfix.ps1
git commit -m "refactor(entrypoint): import module and hand off control with flags"

# Commit 3: docs and assets
git add README.md CHANGELOG.md SECURITY.md assets/logo-vnpcfix.svg
git commit -m "docs: add README, CHANGELOG, SECURITY and logo asset"

# Commit 4: tests
git add tests/*.ps1
git commit -m "test: add Pester unit tests for core, UI, and repairs"

Pop-Location
Write-Host 'Git repository initialized with structured commit history.' -ForegroundColor Green