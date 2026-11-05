$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
if (-not (Test-Path '.venv\Scripts\python.exe')) {
    python -m venv .venv
    & .\.venv\Scripts\python.exe -m pip install -r requirements.txt
}
Write-Host 'Open http://127.0.0.1:18765 in your browser. Ctrl+C to stop.'
& .\.venv\Scripts\python.exe server.py
