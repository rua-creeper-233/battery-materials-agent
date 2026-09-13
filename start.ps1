param(
    [int]$Port = 8765
)

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonCommand = Get-Command python -ErrorAction SilentlyContinue
$pythonExe = if ($pythonCommand) { $pythonCommand.Source } else { $null }

if (-not $pythonExe) {
    $bundledPython = Join-Path $env:USERPROFILE ".cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
    if (Test-Path -LiteralPath $bundledPython) {
        $pythonExe = $bundledPython
    }
}

if (-not $pythonExe) {
    Write-Error "未找到 Python。请安装 Python 3.10+，或在终端中用可用的 Python 运行 server.py。"
    exit 1
}

$url = "http://127.0.0.1:$Port"
Write-Host "Battery Evidence Lab 正在启动：$url"
Write-Host "保持此窗口开启；按 Ctrl+C 停止。"
& $pythonExe (Join-Path $projectRoot "server.py") --port $Port
