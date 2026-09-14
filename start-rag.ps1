param([int]$Port = 8765)

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$endpoint = Read-Host "模型的完整 chat-completions 地址（例如本机 http://127.0.0.1:11434/v1/chat/completions）"
$model = Read-Host "模型名称"
if (-not $endpoint -or -not $model) {
    Write-Error "地址和模型名称不能为空。"
    exit 1
}

$parsed = $null
if (-not [Uri]::TryCreate($endpoint, [UriKind]::Absolute, [ref]$parsed) -or $parsed.Scheme -notin @("http", "https")) {
    Write-Error "请输入完整的 http(s) chat-completions 地址。"
    exit 1
}

Write-Host "若使用远程服务，检索到的论文元数据和短摘录会发送到该地址；PDF文件不会发送。" -ForegroundColor Yellow
$secureKey = Read-Host "API 密钥（本地模型可直接回车）" -AsSecureString
$plainKey = ""
$pointer = [IntPtr]::Zero
try {
    if ($secureKey.Length -gt 0) {
        $pointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureKey)
        $plainKey = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($pointer)
    }
    $env:BATTERY_AGENT_LLM_ENDPOINT = $endpoint
    $env:BATTERY_AGENT_LLM_MODEL = $model
    $env:BATTERY_AGENT_LLM_API_KEY = $plainKey
    & (Join-Path $projectRoot "start.ps1") -Port $Port
} finally {
    if ($pointer -ne [IntPtr]::Zero) { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($pointer) }
    Remove-Item Env:BATTERY_AGENT_LLM_ENDPOINT -ErrorAction SilentlyContinue
    Remove-Item Env:BATTERY_AGENT_LLM_MODEL -ErrorAction SilentlyContinue
    Remove-Item Env:BATTERY_AGENT_LLM_API_KEY -ErrorAction SilentlyContinue
}
