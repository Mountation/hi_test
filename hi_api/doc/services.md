# 服务层日志埋点说明

日期：2025-10-22

概述

- 在服务模块中插入了信息级与警告/错误级日志，用于追踪 CRUD 操作与边界情况。

变更文件

- `hi_api/services/eval_set_service.py`
- `hi_api/services/eval_data_service.py`
- `hi_api/services/eval_result_service.py`

新增内容

- 导入 `logger = get_logger("<component>")`。
- 在 create/list/update/delete 等方法入口处添加 `logger.info(...)`。
- 在未找到对象、异常等分支添加 `logger.warning(...)` 或 `logger.error(...)`。

动机

- 便于观察数据库相关操作的生命周期（创建、删除、更新），用于调试和统计分析。

新增内容（可选）

- 在关键服务方法（尤其是可能触发外部调用的流程）记录耗时：在方法入口记录 start，结束处记录 elapsed，并在日志中输出 `took_ms` 或相似字段，便于聚合慢操作。
- 如果需要端到端链路追踪，建议在 API 层生成 `request_id` 并将其作为上下文传递到服务层与外部请求（例如在 headers 中透传），以便在日志平台中通过 `request_id` 关联多个组件的日志。

如何验证

- 启动后端并调用相应的创建/查询/删除接口。
- 在日志中查找对应方法名与 ID 的输出，确认埋点生效。

注意

- 如需更高价值的链路追踪，可在 API 层生成 request_id 并向下传递到服务层以便关联日志。
- 避免在日志中输出敏感的完整数据；建议记录 ID 与简短说明。

如何定位慢查询或阻塞

- 若怀疑是 DB 查询导致的阻塞，可在服务层临时开启 SQLAlchemy 的 echo 模式或添加针对慢查询的日志（例如记录 SQL 与耗时）。
- 在发生 `ECONNRESET` 或代理断开时，优先在后端日志中查找是否有对应的异常/traceback，再按 timestamp 关联前端 dev server 的 proxy 错误日志以定位问题源头。
