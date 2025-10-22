````markdown
# 日志基础设施

日期：2025-10-22

概述

- 在 `hi_api/utils/log.py` 中添加了基于 `loguru` 的中央日志模块。
- 将 `loguru` 添加到 `hi_api/requirements.txt`。
- 在 `hi_api/main.py` 中接入 logger，用于记录应用启动与关闭事件，并在全局异常处理器中记录未捕获异常与堆栈信息。

变更文件

- `hi_api/utils/log.py` — 新增，用于提供 `get_logger(name)` 封装。
- `hi_api/requirements.txt` — 添加 `loguru` 依赖。
- `hi_api/main.py` — 导入并使用 logger 记录生命周期日志，并在异常处理路径记录堆栈信息。

动机

- 为各模块提供统一且易于配置的日志能力。新增的日志点还记录了关键外部调用的耗时（例如 scoring、AI 客户端调用），便于快速定位慢调用。
- 便于未来添加文件输出、日志切割与结构化日志等功能。

如何验证

1. 安装依赖：

```powershell
pip install -r hi_api/requirements.txt
```

2. 启动 FastAPI 应用，观察控制台是否出现启动日志与未捕获异常的堆栈信息（如触发异常时）。

注意事项

- 文档中避免打印敏感信息；在代码中记录时对 API key 做了遮掩处理。
- 如果需要持久化日志，建议在 `utils/log.py` 中添加文件切割（rotation）方案。
- 在生产环境中建议配置结构化日志输出（JSON）并接入集中式日志平台（例如 ELK / Loki / Datadog），以便进行跨服务聚合与查询。
````
