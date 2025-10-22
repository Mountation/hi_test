# AI 客户端与评分模块埋点说明

日期：2025-10-22

概述

- 在 `hi_api/utils/client.py`（AIClient）和 `hi_api/utils/scoring.py`（AIEval、parse_score、score_answer）中添加了日志埋点。
- 日志包含请求发送、流式事件、解析失败和提取到的分数等信息。

变更文件

- `hi_api/utils/client.py`
  - 使用 `get_logger("AIClient")` 创建 logger。
  - 记录客户端初始化（对 API key 做遮掩）、请求调试信息（仅记录 payload 的 keys）、事件调试信息，以及 workflow 完成或未返回结果时的 info 日志。
  - 在 HTTP 请求失败时记录错误日志。

- `hi_api/utils/scoring.py`
  - 使用 `get_logger("scoring")` 创建 logger。
  - 记录向远端评分服务发送请求、流式事件解析、解析失败情况，以及最终提取到的分数。
  - 在请求异常时记录错误日志。

  新增行为（2025-10-22）

  - 外部 HTTP 请求现在使用共享 `requests.Session`（带重试策略）并遵循来自 `hi_api/config/settings.py` 的超时与最大重试配置。
  - 为避免阻塞事件循环，评分函数在需要时会将同步调用通过 `run_in_executor` 迁移到线程池，从而保证 FastAPI 的异步路由不会被同步请求阻塞。
  - 对关键外部调用（AIClient、scoring）增加了单次调用的 `asyncio.wait_for` 超时保护，超时会被捕获并记录为 `logger.warning`/`logger.error`，并返回可识别的错误给调用方。

  如何调优

  - 编辑 `hi_api/config/config.yaml` 或设置环境变量（例如 `HI_SCORING_BASE_URL`, `HI_SCORING_API_KEY`），并新增如下超时/重试配置键（在 `settings.py` 中可找到默认值）：
    - `external_call_timeout_seconds`：async 调用的 wait_for 超时时间（默认示例：10）
    - `http_timeout_seconds`：底层 requests 调用的超时时间（默认示例：8）
    - `http_max_retries`：requests 重试次数（默认示例：2）

  验证与故障排查

  1. 在日志中查找 `AIEval.eval_ai` / `AIClient` 相关条目，注意 `elapsed` 或 `took` 字段显示的耗时。
  2. 如果遇到 `asyncio.TimeoutError` / wait_for 超时，请根据日志中的 elapsed 值增加 `external_call_timeout_seconds` 或检查评分服务的可用性/性能。
  3. 若频繁出现网络错误（连接重置、连接超时），可以适当增加 `http_max_retries` 并确保评分服务地址在网络上可达。

为什么要这样做

- 这些模块与远端 AI 服务进行流式交互，增加日志有助于定位流中断、意外事件类型或解析问题。

如何复现/验证

1. 确保安装后端依赖：

```powershell
pip install -r hi_api/requirements.txt
```

2. 在 Python 交互环境或测试路由中实例化 `AIClient()`，调用 `get_answer`、`get_intent`，或调用 `score_answer(...)`。
3. 在控制台观察 `AIClient` 与 `scoring` 相关的日志信息，确认事件流和分数被记录。

安全注意事项

- 埋点代码中已遮掩 API key 并避免输出完整请求负载。如需更严格的脱敏，请改为只记录允许的字段白名单。

后续建议

- 在日志中加入结构化字段（如 request_id、eval_id）以便关联多处日志。
- 可在 `utils/log.py` 中启用文件输出与切割以实现持久化日志。
