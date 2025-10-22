# Scoring 服务配置说明

日期：2025-10-22

目的

- 说明如何单独配置评分（scoring）服务的 URL 与 API Key，使其与主 agent 客户端设置独立，便于替换或定向到不同的评分后端。

配置来源优先级

1. 环境变量（HI_ 前缀）
2. 配置文件（hi_api/config/config.yaml 或由环境变量 HI_CONFIG_PATH 指定的路径）
3. 默认值（代码内定义的回退值）

配置字段

- scoring_base_url：评分服务基础地址（例如 `http://scoring-service.local/v1/`）
- scoring_api_key：评分服务的 API Key

回退逻辑

- 若 `scoring_base_url` 未设置，系统会回退使用 `agent_base_url`。
- 若 `scoring_api_key` 未设置，系统会回退使用 `agent_api_key`。

通过配置接口动态管理（推荐开发/测试用）

- 接口：GET /api/v1/config/test
  - 返回格式示例（会包含 scoring 字段）：

```json
{
  "url": "http://agent-base/v1/",
  "api_key": "app-xxx",
  "scoring_url": "http://scoring-service/v1/",
  "scoring_api_key": "scoring-yyy",
  "hotline": "43001",
  "userphone": "11111111111"
}
```

- 接口：PATCH /api/v1/config/test
  - 支持部分字段更新。请求 body 示例（PowerShell）：

```powershell
Invoke-RestMethod -Method Patch -Uri http://127.0.0.1:8000/api/v1/config/test -Body (
  @{ scoring_url = 'http://scoring-service.local/v1/'; scoring_api_key = 'scoring-SECRET' } | ConvertTo-Json
) -ContentType 'application/json'
```

- 接口会把更新写入 YAML 配置文件（默认 `hi_api/config/config.yaml`，可通过环境变量 `HI_CONFIG_PATH` 指定路径），并尝试重新加载运行时设置（so subsequent requests use the new values）。

如何验证

1. 通过命令行直接请求后端（不受 CORS 影响）：

```powershell
Invoke-RestMethod -Method Get -Uri http://127.0.0.1:8000/api/v1/config/test | ConvertTo-Json -Depth 5
```

2. 将 scoring_url 与 scoring_api_key 更新为一个测试实例地址后，触发评分流程（例如调用评分相关接口或运行触发评分的脚本），查看后端日志：`AIEval.eval_ai using url=... api_key_set=yes/no`。

安全与注意事项

- API Key 将以明文写入 YAML。生产环境中请优先使用环境变量注入密钥或使用受控的密钥管理服务。避免将生产密钥直接写入项目内的配置文件。
- 确保配置文件路径和写入权限在部署环境中是安全并受限的。

常见问题

- 配置后不生效：确认已执行 PATCH 写入成功并查看接口返回的 `updated` 字段；若使用了 `get_settings()` 的缓存，PATCH 接口会尝试清除缓存并重载设置；如果仍不生效，重启后端服务确保新配置被加载。
- 若 scoring 服务地址为内部网络地址（container/kubernetes 内部），确保部署环境能路由到该地址。

示例 YAML 片段（`hi_api/config/config.yaml`）

```yaml
agent_base_url: "http://agent-base/v1/"
agent_api_key: "app-xxx"
scoring_base_url: "http://scoring-service/v1/"
scoring_api_key: "scoring-yyy"
default_user_phone: "11111111111"
default_hotline_phone: "43001"
```

改动历史

- 2025-10-22: 添加 scoring 专用字段 `scoring_base_url` / `scoring_api_key`，并在 config API 中暴露 GET/PATCH 支持。
