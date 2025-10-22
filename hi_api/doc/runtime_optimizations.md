```markdown
# 后端运行时优化汇总

日期：2025-10-22

目标

- 提高后端在面对外部不稳定依赖（评分服务、AI agent）时的鲁棒性。
- 避免同步阻塞影响异步路由（FastAPI 事件循环），并对外部调用提供超时与重试策略。
- 提供可配置的运行时参数，方便在不同环境下做调优。

主要改动点

1. 超时保护（per-call）

- 在 API 层对外部调用（AIClient、scoring）使用 `asyncio.wait_for` 包装，超时会被捕获并记录到日志。默认配置键：`external_call_timeout_seconds`。

2. HTTP 层重试与共享 Session

- 使用共享 `requests.Session` 并在底层配置有限重试（`http_max_retries`），以减少短暂网络故障导致的失败。
- 底层 HTTP 超时由 `http_timeout_seconds` 控制（传递给 requests 的 timeout 参数）。

3. 避免阻塞事件循环

- 对于必须使用同步 HTTP 客户端的场景（例如某些评分服务 SDK 只提供同步 API），将这些调用通过 `run_in_executor` 移到线程池执行，从而避免阻塞 FastAPI 的事件循环。

4. 增强日志与计时

- 在关键外部调用周围加入入/出日志，并记录耗时（例如 `logger.info('AIEval.eval_ai finished', took_ms=...)`），便于快速识别慢调用。

如何调整配置

- 修改 `hi_api/config/config.yaml` 或设置环境变量（优先级：env > yaml > 默认值），示例键：
  - `external_call_timeout_seconds`: 事件循环中等待外部调用完成的超时时间（秒）。
  - `http_timeout_seconds`: 底层 requests 的 socket/connect/read 超时时间（秒）。
  - `http_max_retries`: 底层 HTTP 的重试次数。

验证步骤（Smoke tests）

1. 启动后端并访问健康检查：

```powershell
Invoke-RestMethod -Method Get -Uri http://127.0.0.1:8000/api/v1/health | ConvertTo-Json
```

2. 触发需要外部评分的流程（或使用一个可控的 mock scoring URL）并观察日志条目，确认 `took_ms` / elapsed 字段记录并且超时行为按预期触发。

3. 若遇到超时，利用日志中记录的耗时数据来合理调整 `external_call_timeout_seconds` 与 `http_timeout_seconds`。

常见故障与建议

- 频繁超时：先检查评分服务本身的响应时间，再酌情增加超时时间；避免把超时设置得过大，以免资源被长时间占用。
- 出现大量重试失败：检查网络连通性与评分服务稳定性，并考虑配置熔断或后备方案（例如返回默认分数或记录失败以便稍后重试）。

下一步建议

- 将日志输出接入集中式日志平台以便跨请求聚合并设置告警（例如长时间平均延迟上升）。
- 在关键路径引入指标（Prometheus）以实现实时监控和告警。

```