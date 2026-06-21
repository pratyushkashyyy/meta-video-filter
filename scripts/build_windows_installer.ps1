param(
    [string]$Python = "python",
    [string]$InnoSetupCompiler = "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe"
)

$ErrorActionPreference = "Stop"

Set-Location (Split-Path -Parent $PSScriptRoot)

if (-not (Test-Path "venv")) {
    & $Python -m venv venv
}

& .\venv\Scripts\python.exe -m pip install -U pip setuptools wheel
& .\venv\Scripts\python.exe -m pip install -r requirements-dev.txt
& .\venv\Scripts\python.exe -m pytest -q
& .\venv\Scripts\pyinstaller.exe MetaVideoFilter.spec --clean --noconfirm

if (-not (Test-Path $InnoSetupCompiler)) {
    throw "Inno Setup compiler not found at '$InnoSetupCompiler'. Install Inno Setup 6 or pass -InnoSetupCompiler."
}

New-Item -ItemType Directory -Force -Path release | Out-Null
& $InnoSetupCompiler installer\MetaVideoFilter.iss

Write-Host "Installer built in .\release"
