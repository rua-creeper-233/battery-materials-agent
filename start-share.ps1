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
    Write-Error "未找到带 pypdf 的 Python。请先运行：python -m pip install -r requirements.txt"
    exit 1
}

$cloudflaredCommand = Get-Command cloudflared -ErrorAction SilentlyContinue
if (-not $cloudflaredCommand) {
    Write-Error "未找到 cloudflared。请先运行：winget install --id Cloudflare.cloudflared"
    exit 1
}

$accessKey = [Convert]::ToHexString([Security.Cryptography.RandomNumberGenerator]::GetBytes(24)).ToLowerInvariant()
$serviceUrl = "http://127.0.0.1:$Port"
$previousAccessKey = $env:BATTERY_AGENT_ACCESS_TOKEN
$env:BATTERY_AGENT_ACCESS_TOKEN = $accessKey
$serverProcess = Start-Process -FilePath $pythonExe -ArgumentList @(
    (Join-Path $projectRoot "server.py"),
    "--port", "$Port",
    "--public-api",
    "--allowed-origin", "https://rua-creeper-233.github.io"
) -WorkingDirectory $projectRoot -WindowStyle Hidden -PassThru
if ($null -eq $previousAccessKey) {
    Remove-Item Env:BATTERY_AGENT_ACCESS_TOKEN -ErrorAction SilentlyContinue
} else {
    $env:BATTERY_AGENT_ACCESS_TOKEN = $previousAccessKey
}

Write-Host ""
Write-Host "Battery Evidence Lab 共享模式已启动。" -ForegroundColor Green
Write-Host "1. 保持此窗口开启。"
Write-Host "2. 下面会出现 https://...trycloudflare.com 地址。"
Write-Host "3. 在 GitHub 页面点“上传文献”，填入该地址和以下临时访问密钥："
Write-Host ""
Write-Host $accessKey -ForegroundColor Yellow
Write-Host ""
Write-Host "访问密钥只在本次运行有效；请只发给导师。按 Ctrl+C 会同时关闭共享服务。"
Write-Host ""

try {
    & $cloudflaredCommand.Source tunnel --url $serviceUrl
} finally {
    if ($serverProcess -and -not $serverProcess.HasExited) {
        Stop-Process -Id $serverProcess.Id -ErrorAction SilentlyContinue
    }
}
