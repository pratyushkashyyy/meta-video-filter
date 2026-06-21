param(
    [string]$Python = "py",
    [string[]]$PythonArgs = @("-3.10"),
    [string]$FfmpegPath = "",
    [string]$InnoSetupCompiler = "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe"
)

$ErrorActionPreference = "Stop"

Set-Location (Split-Path -Parent $PSScriptRoot)

function Invoke-Native {
    param(
        [string]$FilePath,
        [string[]]$Arguments
    )

    & $FilePath @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed with exit code $LASTEXITCODE`: $FilePath $($Arguments -join ' ')"
    }
}

function Resolve-Ffmpeg {
    param([string]$ExplicitPath)

    if ($ExplicitPath) {
        if (-not (Test-Path $ExplicitPath)) {
            throw "ffmpeg.exe was not found at '$ExplicitPath'."
        }
        return (Resolve-Path $ExplicitPath).Path
    }

    $command = Get-Command ffmpeg.exe -ErrorAction SilentlyContinue
    if ($command) {
        return $command.Source
    }

    $commonPaths = @(
        "$env:LOCALAPPDATA\Microsoft\WinGet\Packages\Gyan.FFmpeg_*\ffmpeg-*\bin\ffmpeg.exe",
        "$env:LOCALAPPDATA\Microsoft\WinGet\Packages\BtbN.FFmpeg_*\ffmpeg-*\bin\ffmpeg.exe",
        "$env:ProgramData\chocolatey\bin\ffmpeg.exe",
        "C:\ffmpeg\bin\ffmpeg.exe"
    )

    foreach ($pattern in $commonPaths) {
        $match = Get-ChildItem -Path $pattern -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($match) {
            return $match.FullName
        }
    }

    return $null
}

if (-not (Test-Path "venv")) {
    $VenvArgs = @($PythonArgs) + @("-m", "venv", "venv")
    Invoke-Native $Python $VenvArgs
}

$VenvPython = ".\venv\Scripts\python.exe"
$PythonVersion = (& $VenvPython -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')").Trim()
if ($PythonVersion -ne "3.10") {
    throw "The build venv uses Python $PythonVersion. Delete .\venv and rerun with Python 3.10."
}

Invoke-Native $VenvPython @("-m", "pip", "install", "-U", "pip", "setuptools", "wheel")
Invoke-Native $VenvPython @("-m", "pip", "install", "-r", "requirements-dev.txt")
Invoke-Native $VenvPython @("-m", "pytest", "-q")
Invoke-Native ".\venv\Scripts\pyinstaller.exe" @("MetaVideoFilter.spec", "--clean", "--noconfirm")

if (-not (Test-Path $InnoSetupCompiler)) {
    throw "Inno Setup compiler not found at '$InnoSetupCompiler'. Install Inno Setup 6 or pass -InnoSetupCompiler."
}

New-Item -ItemType Directory -Force -Path release | Out-Null

$ResolvedFfmpeg = Resolve-Ffmpeg -ExplicitPath $FfmpegPath
if (-not $ResolvedFfmpeg) {
    throw "ffmpeg.exe was not found. Install FFmpeg with 'winget install Gyan.FFmpeg' or pass -FfmpegPath 'C:\ffmpeg\bin\ffmpeg.exe'."
}

Copy-Item -Force $ResolvedFfmpeg ".\dist\MetaVideoFilter\ffmpeg.exe"
Write-Host "Bundled ffmpeg.exe from $ResolvedFfmpeg"

Invoke-Native $InnoSetupCompiler @("installer\MetaVideoFilter.iss")

Write-Host "Installer built in .\release"
