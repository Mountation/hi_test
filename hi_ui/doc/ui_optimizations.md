# 前端 UI 优化与 Ant Design 迁移记录

日期：2025-10-22

## 概述
本次迭代目标：统一前端界面风格、提升首屏感知速度、并将若干页面迁移到 Ant Design（AntD）以获得稳定、可复用的组件与一致的视觉语言。改动优先保留现有业务逻辑与 API 调用，仅替换视图与部分交互展示方式。

核心成果：
- 采用 Ant Design 组件替换原生元素（Input, Button, Table, Upload, Form 等），统一样式与交互。
- 抽象并复用了 `ErrorBanner` 组件（基于 AntD Alert）用于页面错误展示（可自动隐藏、可手动关闭）。
- 增加骨架/占位、Collapse/List 细节展示，提升加载与错误的可见性。

## 变更范围（主要页面）

- `src/pages/EvalSetsPage.tsx` — AntD `Table`, `Input.Search`, `Card`, `Skeleton`, `Collapse`，以及使用 `ErrorBanner` 展示错误。
- `src/pages/EvalDataPage.tsx` — AntD `Form`, `Input`, `Table`, `Button`, `Popconfirm`，保留新增/删除/执行功能。
- `src/pages/ResultsSetPage.tsx`、`src/pages/ResultsDataPage.tsx` — AntD `Table`/`Button` 以统一结果展示。
- `src/pages/MultiExecutePage.tsx` — AntD `InputNumber`, `Checkbox`, `List`, `Card`, `Button`，保留多集并发执行逻辑。
- `src/pages/UploadExcelPage.tsx` — AntD `Upload` + manual `beforeUpload` + `Button`（手动提交以调用后端 `uploadExcel`）。
- `src/pages/ConfigPage.tsx` — AntD `Form`, `Input`, `Button` 用于配置管理。
- `src/pages/Users.tsx`, `src/pages/Items.tsx`, `src/pages/Home.tsx`, `src/pages/Me.tsx` — 用 `Card`/`List` 提升展示一致性。

## 关键组件

- `src/components/ErrorBanner.tsx` — 统一错误横幅（基于 AntD `Alert`），支持 `type`, `durationMs`, `onClose`。

## 行为/UX 说明

- 错误从阻塞式 `alert()` 替换为非阻塞可关的 `ErrorBanner`，默认 8 秒自动隐藏。
- 表格、表单与按钮采用 AntD 风格，交互如创建/删除/执行仍走原有 API。
- 上传流程：选择文件后不自动上传，用户点击“上传”按钮触发 `api.uploadExcel(file)`。

## 开发与运行（PowerShell）

从项目根或 `hi_ui` 文件夹，执行：
```powershell
cd E:\AIEval\hi_test\hi_ui
npm install
npm run dev
```

注意事项：
- 项目现在依赖 `antd` 和 `@ant-design/icons`，确保 `npm install` 成功。
- AntD 样式已在 `src/main.tsx` 中引入：`import 'antd/dist/reset.css'`。

## 验证要点

1. 访问 `/sets`：应看到 AntD 表格与骨架（加载中）而非空白。
2. 制造错误（例如后端关闭）应触发 `ErrorBanner`，可手动关闭或等待 8 秒自动隐藏。
3. 表单（新增评测数据、配置保存）应显示 AntD 按钮与输入，操作结果通过 `message` 或横幅反馈。

## 回滚策略

- 回退：在 Git 中 revert 对应提交或还原文件到旧版本，或临时从 `src/main.tsx` 移除 AntD 样式引用。

## 后续建议

1. 将重复布局抽象为共享组件（`PageCard`, `SkeletonCard`, `FormRow`）。
2. 使用 React Query / SWR 管理请求与缓存，自动重试与失效处理更便捷。
3. 增加单元/集成测试覆盖核心页面与 API 调用（尤其是批量执行流程）。

---
已完成的工作清单（本次提交）:

- 迁移并统一样式于主要页面（见上方列表）。
- 添加并复用 `ErrorBanner`。
- 更新 `README.md` 以说明 AntD 依赖与运行步骤（见仓库根 README）。

如需我继续：我可以（按优先级）完成剩余页面的微调（将 `details` → `Collapse` 替换、去除内联样式、统一按钮尺寸等），或帮你在本地跑一遍 `npm run dev` 并修复出现的任何样式或类型问题。