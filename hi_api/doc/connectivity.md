# 前端与后端连通性 (Failed to fetch) 排查与解决

日期：2025-10-22

场景回顾

- 问题：浏览器前端页面在加载评测集时弹出错误 `加载评测集失败: Failed to fetch`，页面无法显示评测集。
- 初步判断：这属于前端无法拿到后端响应的典型表现，可能原因包括后端未运行、端口监听问题、Vite 代理配置错误或浏览器的跨域 (CORS) 限制。

已采取的操作

1. 确认后端路由存在

- 后端文件 `hi_api/api/eval_sets_api.py` 已实现 `/`、`POST /`、`GET /{id}` 等路由，并在 `hi_api/main.py` 中以前缀 `/api/v1/evalsets` 注册。

2. 本地端口与请求检测

- 使用 PowerShell 的 `Get-NetTCPConnection -LocalPort 8000` 与 `Invoke-RestMethod` 来检测后端是否在本机监听并返回评测集。
- 结果显示：在最开始的检查时并未检测到 8000 端口的监听（即后端没启动），后来用户确认并启动了后端。

3. 添加并启用 CORS

- 为避免浏览器阻止跨域请求，我们在 `hi_api/main.py` 中加入了 `fastapi.middleware.cors.CORSMiddleware`，允许 `http://localhost:3000` 和 `http://localhost:5173` 等开发地址访问后端。
- 修改后需要重启后端进程以使设置生效。

4. 前端辅助改造（帮助定位问题）

- 在 `hi_ui/src/pages/EvalSetsPage.tsx` 中将加载函数 `load()` 包裹到 try/catch 并在失败时 `alert()` 错误信息，避免静默失败，便于观察后端返回错误或浏览器错误。
- 提示：浏览器控制台 Network 面板是判断是否为 CORS 的关键（如果是 CORS 导致，会看到明显的被浏览器阻断的错误信息）。

如何验证问题已解决

1. 启动后端（示例 PowerShell）

```powershell
cd E:\AIEval\hi_test
uvicorn hi_api.main:app --reload --host 127.0.0.1 --port 8000
```

2. 在同一台机器直接用命令行请求（这不会受 CORS 限制）

```powershell
Invoke-RestMethod -Method Get -Uri http://127.0.0.1:8000/api/v1/evalsets/ | ConvertTo-Json -Depth 5
```

- 若此命令成功返回 JSON，则说明后端本身正常工作；若失败请检查后端日志以定位错误（例如数据库连接失败、依赖缺失等）。

3. 在浏览器中访问前端页面并打开开发者工具 → Network

- 刷新页面并观察 `/api/v1/evalsets/` 请求的响应状态与响应头。
- 若响应被浏览器阻止，会看到 CORS 错误；若返回 200 但页面仍不显示，请检查前端控制台的 JS 错误与类型错误。

快速调试技巧

- 临时绕过代理：将 `hi_ui/src/api/client.ts` 中的 `BASE` 设置为 `http://127.0.0.1:8000`，这样前端会直接请求后端（适用于本机开发调试）。
- 若临时绕过可成功，则说明问题与 Vite 代理配置或 dev server 有关；若仍失败，则是后端或网络问题。

代理（ECONNRESET）诊断建议

- 如果在前端 dev server 控制台看到类似 `http proxy error: /api/v1/evalsets/ Error: read ECONNRESET`，请同时查看后端日志中与该请求时间点接近的异常或错误条目（按 timestamp 关联），确认是否为后端抛出异常或线程阻塞导致连接被重置。
- 在后端中临时将 `utils/client.py` 和 `utils/scoring.py` 的日志等级调到 DEBUG，以记录外部 HTTP 请求的开始/结束与耗时，便于复现时快速定位是网络中断还是后端内部异常。
- 若后端在处理请求的过程中执行了耗时的外部调用（例如 scoring 服务超时），可以临时加大 `external_call_timeout_seconds` 或在本地替换为一个快速可达的 mock URL 以确认请求链路完整性。

示例：临时绕过并确认流程

1. 将前端直接指向后端：在 `hi_ui/src/api/client.ts` 设置 `BASE = 'http://127.0.0.1:8000'`。
2. 在后端启动并在 PowerShell 中运行：

```powershell
Invoke-RestMethod -Method Get -Uri http://127.0.0.1:8000/api/v1/evalsets/ | ConvertTo-Json -Depth 5
```

3. 若命令成功而前端仍报 `ECONNRESET`，可以重启前端 dev server（确保代理配置刷新）并再次尝试；若两者都失败，请在后端开启更详细日志并重试。 

后续建议

- 在生产环境不要使用开放的 CORS 白名单，生产应仅允许可信来源。
- 在前端加入更友好的错误展示（例如顶部横幅），并在后端日志中加入 request_id 以便在日志和前端错误间建立关联。
