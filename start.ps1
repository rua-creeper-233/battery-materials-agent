param(
    [int]$Port = 8765
)

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonCandidates = @(
    (Join-Path $projectRoot ".venv\Scripts\python.exe"),
    ((Get-Command python -ErrorAction SilentlyContinue).Source),
    (Join-Path $env:USERPROFILE ".cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe")
) | Where-Object { $_ -and (Test-Path -LiteralPath $_) } | Select-Object -Unique
$pythonExe = $null
foreach ($candidate in $pythonCandidates) {
    & $candidate -c "import pypdf" 2>$null
    if ($LASTEXITCODE -eq 0) { $pythonExe = $candidate; break }
}

if (-not $pythonExe) {
    Write-Error "未找到带 pypdf 的 Python。请在项目目录运行：python -m pip install -r requirements.txt"
    exit 1
}

$url = "http://127.0.0.1:$Port"
Write-Host "Battery Evidence Lab 正在启动：$url"
Write-Host "保持此窗口开启；按 Ctrl+C 停止。"
& $pythonExe (Join-Path $projectRoot "server.py") --port $Port
