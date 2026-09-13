# GitHub Pages＋本地科研服务共享指南

## 先分清两部分

```text
导师浏览器
├─ 打开固定网址 ──> GitHub Pages（HTML/CSS/JS、40 篇公开元数据）
└─ 带临时密钥调用 ──> HTTPS Tunnel ──> 你电脑的 127.0.0.1:8765
                                          ├─ 上传 PDF
                                          ├─ 全文与关键词索引
                                          └─ 本地科研问答
```

GitHub Pages 是静态托管，不能直接运行 Python。它适合提供固定入口；需要上传、全文检索和关键词提取时，再由浏览器通过 HTTPS 隧道调用你电脑上的服务。

固定网页：<https://rua-creeper-233.github.io/battery-materials-agent/>

## 场景一：只让导师浏览

直接把固定网页发给导师即可。你的电脑可以关机，导师仍能查看 40 篇论文元数据、DOI/WOS 入口和静态规则问答。

限制：不能上传论文，不能访问你刚加入的私人文献，也不能使用本地全文检索。

## 场景二：临时开放上传与本地检索

最简单的方法是双击项目根目录的 `start-share.bat`。它会打开 GitHub Pages，并调用下面的 PowerShell 共享脚本；窗口必须保持开启。

### 第一次准备

1. 安装 Python 依赖：

   ```powershell
   python -m pip install -r requirements.txt
   ```

2. 安装 Cloudflare Tunnel：

   ```powershell
   winget install --id Cloudflare.cloudflared
   ```

3. 关闭并重新打开 PowerShell，让 `cloudflared` 进入命令搜索路径。

### 每次与导师共享

1. 在项目目录运行：

   ```powershell
   .\start-share.ps1
   ```

   如果 PowerShell 阻止脚本执行，可运行：

   ```powershell
   powershell -NoProfile -ExecutionPolicy Bypass -File .\start-share.ps1
   ```

2. 终端先显示一串临时访问密钥，随后显示形如 `https://random-name.trycloudflare.com` 的地址。
3. 打开固定 GitHub 网页，点击右上角“上传文献”。
4. 填入隧道地址和临时访问密钥，点击“测试连接”。
5. 连接成功后选择 PDF；标题、DOI、年份、期刊和作者可以手工补充，也可以留空让程序尝试识别。
6. 把固定 GitHub 网页、当次隧道地址和当次访问密钥通过可信渠道发给导师。
7. 用完后在共享终端按 `Ctrl+C`。隧道、本地服务和访问密钥一起失效。

必须满足：你的电脑保持开机、联网，共享终端保持运行。Quick Tunnel 地址每次启动都会变化，适合演示、组会和短期协作，不适合无人值守的长期服务。

## 安全边界

- 跨域来源只允许 `https://rua-creeper-233.github.io`；
- 远程 API 请求必须带当次随机访问密钥；
- 密钥不写入 Git，只保存在当前浏览器标签页；
- 远程访问永远拿不到 Zotero 条目键和附件键；
- 远程访问不能下载或打开你电脑里的 PDF；
- 上传 PDF 和新增文献元数据位于 Git 忽略目录，不会进入 GitHub Pages；
- 单个上传文件上限为 50 MiB，已有不同 PDF 时不会静默覆盖。

即使有这些限制，也只应把访问密钥发给可信的导师或组员，并在不用时关闭共享进程。

## 场景三：长期稳定的本地后端地址

固定 GitHub 网页不需要变化；变化的是 API 地址。若不想每次填写新的 `trycloudflare.com` 地址，需要：

1. 准备一个由 Cloudflare 管理 DNS 的自有域名；
2. 创建 named Cloudflare Tunnel；
3. 把例如 `battery-api.example.com` 路由到 `http://127.0.0.1:8765`；
4. 让 `cloudflared` 作为 Windows 服务运行；
5. 在服务前增加 Cloudflare Access，或继续保留本项目的访问密钥；
6. 仍要保证你的电脑长期在线。

如果没有自有域名，先使用 Quick Tunnel。不要把 Python 服务直接绑定到公网网卡，也不要在路由器上裸开 8765 端口。

## API 接口

- `GET /api/health`：服务状态；
- `GET /api/capabilities`：上传限制、关键词接口版本和隐私策略；
- `POST /api/upload`：`multipart/form-data` 上传 PDF；
- `POST /api/keywords`：传 `text` 或 `paper_id`，返回版本化关键词结果；
- `POST /api/chat`：调用本地全文检索与回答。

关键词接口当前为 `v1`，提供者为 `builtin-domain-frequency`。以后可以在后端替换为 KeyBERT、LLM 或专门的材料科学模型，网页端无需更改请求路径。

## 官方参考

- GitHub Pages 是静态站点托管：<https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages>
- Cloudflare Quick Tunnel：<https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/do-more-with-tunnels/trycloudflare/>
- 正式 Cloudflare Tunnel 配置：<https://developers.cloudflare.com/tunnel/setup/>
