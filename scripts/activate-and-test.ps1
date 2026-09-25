<#
Activate repository root .venv and run tests.
Leaves the PowerShell session with the venv activated so new shells stay activated when you use this script as your terminal profile command.

Usage: From repository root in PowerShell run:
  .\scripts\activate-and-test.ps1

This script intentionally does not change the execution policy permanently.
#>
param()

Set-StrictMode -Version Latest
try {
    $venvActivate = Join-Path -Path $PSScriptRoot -ChildPath "..\.venv\Scripts\Activate.ps1"
    if (-Not (Test-Path $venvActivate)) {
        Write-Host "Root .venv not found. Creating with Python 3.11..."
        py -3.11 -m venv ..\.venv
    }

    Write-Host "Activating .venv..."
    # dot-source the Activate.ps1 so the current session is modified
    . $venvActivate

    Write-Host "Upgrading pip and installing dependencies (if needed)..."
    python -m pip install --upgrade pip
    python -m pip install -r ..\services\api\requirements.txt

    Write-Host "Running backend tests..."
    python -m pytest -q ..\services\api

    Write-Host "Virtual environment is active in this shell. Run commands as needed."
} catch {
    Write-Error "Failed to activate venv or run tests: $_"
    exit 1
}
