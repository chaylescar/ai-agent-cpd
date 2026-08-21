#! powershell
#Requires -Version 5.1
<#
.SYNOPSIS
  Install uv (if needed), pin Python, and create .venv in this repo.
#>
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

function Find-Uv {
    $cmd = Get-Command uv -ErrorAction SilentlyContinue
    if ($cmd) {
        return $cmd.Source
    }
    $candidates = @(
        (Join-Path $env:USERPROFILE ".local\bin\uv.exe"),
        (Join-Path $env:USERPROFILE ".cargo\bin\uv.exe"),
        (Join-Path $env:LOCALAPPDATA "Programs\uv\uv.exe")
    )
    foreach ($path in $candidates) {
        if (Test-Path $path) {
            return $path
        }
    }
    return $null
}

Write-Host "Workshop bootstrap"
Write-Host "  repo: $Root"

$uv = Find-Uv
if (-not $uv) {
    Write-Host "  uv not found - installing (user-local, no admin)..."
    Invoke-RestMethod https://astral.sh/uv/install.ps1 | Invoke-Expression
    $localBin = Join-Path $env:USERPROFILE ".local\bin"
    $cargoBin = Join-Path $env:USERPROFILE ".cargo\bin"
    $env:Path = "$localBin;$cargoBin;$env:Path"
    $uv = Find-Uv
    if (-not $uv) {
        throw "uv was installed but is not on PATH. Close this terminal, open a new one, and re-run bootstrap.ps1."
    }
}

Write-Host "  uv: $uv"
$pyVersion = (Get-Content -Path .python-version -Raw).Trim()
Write-Host "  ensuring Python ${pyVersion} is available"
Write-Host "  (cached user-wide; skipped if already installed)"
& $uv python install
if ($LASTEXITCODE -ne 0) {
    throw "uv python install failed."
}

Write-Host "  creating .venv and installing dependencies..."
& $uv sync
if ($LASTEXITCODE -ne 0) {
    throw "uv sync failed."
}

$python = Join-Path $Root ".venv\Scripts\python.exe"
Write-Host ""
Write-Host "Ready."
Write-Host "  interpreter: $python"
Write-Host ""
Write-Host "Next steps:"
Write-Host "  1. Open this folder in VS Code."
Write-Host "  2. Install the recommended extensions when prompted."
Write-Host "  3. Press F5 to launch the arcade menu in the integrated terminal."
Write-Host "  Or run:  uv run workshop"
Write-Host ""
