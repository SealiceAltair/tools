param([string]$Python = "python", [string]$BuildTools = "")

$ErrorActionPreference = "Stop"
$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Push-Location $ProjectDir
try {
    $PreviousPythonPath = $env:PYTHONPATH
    if ($BuildTools) { $env:PYTHONPATH = $BuildTools }
    & $Python -m PyInstaller --noconfirm --clean --onefile --windowed `
        --name "ほしみのダイスロール" `
        --distpath ".\完成品" `
        --workpath ".\build" `
        --specpath "." `
        ".\app.py"
    if ($LASTEXITCODE -ne 0) {
        throw "アプリの作成に失敗しました。"
    }
}
finally {
    $env:PYTHONPATH = $PreviousPythonPath
    Pop-Location
}
