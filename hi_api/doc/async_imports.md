# 异步导入（Job-based Upload）说明

日期：2025-10-22

概述

为了解决大文件（Excel）上传时同步解析与逐行写入导致的慢、阻塞和 500 超时问题，我们将导入流程改为基于后台任务的异步导入：

- 上传端点现在立即返回一个 `job_id`，并在后台处理文件。
- 后台任务以流式方式读取 Excel（openpyxl read_only），按 batch（默认 500）做批量插入，显著提高吞吐。
- 前端轮询 `GET /api/v1/jobs/{job_id}` 获取进度并显示进度条。

核心改动

- 新增 DB 模型 `Job`（表名 `jobs`）：
  - 字段：`job_id, eval_set_id, status, processed, total, file_path, error, created_at, started_at, finished_at`
- 修改上传接口：
  - `POST /api/v1/evalsets/upload`：保存上传文件到临时目录，创建 `Job` 记录并返回 `{ job_id, eval_set_id }`，通过 FastAPI `BackgroundTasks` 或线程触发后台处理。
- 新增后台处理器：
  - `hi_api/services/upload_job_worker.py`：`process_upload_job(job_id)`，按批插入（使用 SQLAlchemy core insert）并在每个批次更新 `Job.processed` 与 `Job.total`。
- 新增 Job 状态查询接口：
  - `GET /api/v1/jobs/{job_id}`：返回 `{ job_id, status, processed, total, error }`，供前端轮询。
- Dev helper：
  - `POST /api/v1/jobs/create_tables`：运行 SQLAlchemy `Base.metadata.create_all`（用于在开发/测试环境创建 `jobs` 表）。

前端配合（已实现）

- `hi_ui/src/api/client.ts`：新增 `getJobStatus(jobId)`。
- `hi_ui/src/pages/UploadExcelPage.tsx`：上传后如果返回 `job_id` 则开始每 1.5s 轮询 `getJobStatus(jobId)`，并使用 AntD `Progress` 显示百分比。

如何在本地验证（开发步骤）

1. 启动后端（确保 `DATABASE_URL` 可达）：

```powershell
Set-Location 'E:\AIEval\hi_test\hi_api'
python -m uvicorn main:app --reload
```

2. （若尚未创建 `jobs` 表）调用创建表的 helper：

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/v1/jobs/create_tables
```

3. 在前端 UI 上传 Excel 文件（或使用 API 客户端）：

- 前端会收到 `{ job_id, eval_set_id }`。
- 前端开始轮询 `GET /api/v1/jobs/{job_id}`，将 `processed/total` 转为百分比显示。

4. 后台任务完成后：
- `Job.status` 将为 `success` 或 `failed`，并且 `job.error` 会包含错误详情（若失败）。
- `eval_set_service.refresh_count(eval_set_id)` 会在后台被调用更新评测集计数。

操作注意事项与建议

- 目前后台执行使用 FastAPI 的 `BackgroundTasks` 或线程作为回退，这适用于轻量开发，但不保证任务持久化或在进程重启后恢复。如果你需要可靠、可扩展的队列，请考虑引入 Celery / Redis（或 RQ）并执行任务的独立 worker 进程。
- 对于非常大的文件（数十万行），使用数据库原生的高效加载接口（MySQL `LOAD DATA INFILE` 或 Postgres `COPY`) 会更快。当前实现以通用 SQLAlchemy 插入为主，已显著快于逐行 ORM 插入。
- 如果你需要提前获取精确的 `total` 行数，可在后台任务开始时对文件做一次简单计数（tradeoff：额外 I/O）。当前实现是流式读取并在处理时逐步累加 `total`。

故障排查

- 若上传立即返回 500：首先确认 `jobs` 表是否存在（参见第 2 步）。如果表不存在，会导致 `session.add(job)` 抛错。
- 若 DB 连接失败：检查 `DATABASE_URL` 环境变量并确保数据库可达。
- 若后台任务失败：查看后端控制台日志，任务异常会被记录并写入 `job.error` 字段。

下一步建议

- 将 `BackgroundTasks` 替换为生产级队列（Celery + Redis）并提供 worker systemd 或 supervisor 脚本。
- 添加一个 pytest 集成测试，使用 in-memory sqlite 测试上传 + 轮询流程。
- （可选）支持前端上传分块（multipart/chunked）以处理超大文件与暂停/恢复。

