$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$env:PYTHONUTF8 = '1'
$choices = @(
    @{Exe=(Join-Path $PSScriptRoot '.venv\Scripts\python.exe'); Prefix=@()},
    @{Exe='py'; Prefix=@('-3')},
    @{Exe='python'; Prefix=@()},
    @{Exe='python3'; Prefix=@()}
)
foreach ($choice in $choices) {
    if (-not (Get-Command $choice.Exe -ErrorAction SilentlyContinue)) { continue }
    $exe = $choice.Exe
    $prefix = $choice.Prefix
    & $exe @prefix -c "import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)" 2>$null
    if ($LASTEXITCODE -ne 0) { continue }
    & $exe @prefix (Join-Path $PSScriptRoot 'launcher.py')
    exit $LASTEXITCODE
}
Write-Host 'Python 3.10+ was not found. Install Python from https://www.python.org/downloads/ and try again.' -ForegroundColor Yellow
exit 1
