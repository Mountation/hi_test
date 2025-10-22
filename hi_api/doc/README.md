# 项目优化文档

本目录按时间顺序收集每次优化操作的 Markdown 说明。每个文件记录变更内容、变更原因以及如何复现或验证。


文件列表：

- `logging.md` — 中央日志基础设施和使用说明。
- `services.md` — 在服务层（eval_set、eval_data、eval_result）中添加的日志埋点说明。
- `client_scoring.md` — AI 客户端和评分工具的日志埋点说明。
- `frontend.md` — 前端脚手架说明及后续界面改进计划。
- `connectivity.md` — 前端与后端连通性问题（Failed to fetch）的排查与解决步骤。
- `frontend_api_changes.md` — 前端 API 客户端 (`hi_ui/src/api/client.ts`) 的改动说明与类型修正。
- `async_imports.md` — 基于后台任务的 Excel 异步导入实现与使用说明（jobs 表、job 状态查询、开发建表 helper 等）。

生成时间：2025-10-22
