# 2025-10-24 — Cleanup task & display_index sync

日期：2025-10-24

变更概述

- 新增定期清理服务 `cleanup_service`，用于永久删除数据库中 `deleted = true` 的行（`eval_results`, `eval_data`, `eval_set`）。
- 为 `eval_set` 引入 `display_index` 展示字段，并保证 API 返回按 `display_index` 排序；前端提供了回退显示以兼容未初始化的运行时数据库。

目的

- 释放被软删除数据占用的空间并保持表整洁。
- 提供可递补的展示序号 `display_index`，避免修改主键 id，同时支持删除后对展示序号的前移递补。

代码变更（要点）

- 新增服务：`hi_api/services/cleanup_service.py`
  - 导出 `run_cleanup(dry_run=False)`：一次性运行清理，dry_run=True 时仅统计并返回待清理行数。
  - 导出 `schedule_cleanup(interval_seconds)`：循环调度器，按指定间隔运行 `run_cleanup`。
  - 实现细节：按表分块删除（默认每批 500 行），每批删除后短暂 sleep（0.05s）以减小锁竞争风险。

- 应用启动钩子：`hi_api/main.py`
  - 在 `startup` 事件中，如果环境变量 `CLEANUP_ENABLED` 为 `1|true`，会在后台线程启动 `schedule_cleanup`。
  - 调度间隔可通过 `CLEANUP_INTERVAL_SECONDS` 配置（单位：秒，默认 86400，即 1 天）。

- display_index 相关：
  - DDL: `hi_api/data/create_eval_set.sql` 已包含 `display_index INT NOT NULL DEFAULT 0`（若你的运行数据库未修改，请运行 ALTER TABLE 以添加该列）。
  - ORM: `hi_api/db/models.py` 中 `EvalSet` 添加了 `display_index` 字段。
  - API: Pydantic 模型（`hi_api/models/eval_set.py`）已包含 `display_index`，并在 `hi_api/services/eval_set_service.py` 保证 `list_eval_sets` 按 `display_index` 排序返回。
  - 前端: `hi_ui/src/pages/EvalSetsPage.tsx` 将表格第一列改为显示 `display_index`，并在后端未初始化该字段时回退显示为 `id`。

运行与验证指南

1) 在运行库中先做一次 dry-run（建议）：

```powershell
python -c "from services.cleanup_service import run_cleanup; print(run_cleanup(dry_run=True))"
```

2) 若满意，再手动运行一次清理（或启用调度器）：

手动一次性执行：
```powershell
python -c "from services.cleanup_service import run_cleanup; print(run_cleanup(dry_run=False))"
```

启用定期调度并重启后端（示例 PowerShell 环境变量设置）：
```powershell
$env:CLEANUP_ENABLED = '1'
$env:CLEANUP_INTERVAL_SECONDS = '86400'
# 重启你的 FastAPI 服务（例如重新运行 uvicorn）
```

3) display_index 数据库迁移（若你的运行库尚未包含该列）：

```sql
ALTER TABLE eval_set ADD COLUMN display_index INT NOT NULL DEFAULT 0 COMMENT '展示顺序，用于前端显示/排序，可递补';
SET @i = 0;
UPDATE eval_set SET display_index = (@i := @i + 1) ORDER BY id;
```

注意与建议

- 删除为永久操作，请在执行前确认备份策略。若你希望保留历史记录，我可以改为把被删行移动到 `archive_*` 表而不是直接删除。
- 当前实现按顺序删除 `eval_results` -> `eval_data` -> `eval_set`。如果你有外键或触发器，或需要调整顺序，请告知。
- 对于非常大的表，考虑把批量大小和 sleep 时间调整为更保守的值，或运行在低峰时段。

后续改进建议

- 提供基于删除时间的保留策略（例如仅删除已被标记 deleted 且 updated_at < now() - INTERVAL 30 DAY）。
- 将清理脚本移入运维工具（例如用 Alembic 管理变更，或放入运维 cron/CI）并加入日志轮转/报警。
