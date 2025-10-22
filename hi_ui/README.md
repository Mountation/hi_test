# hi_ui

基于 Vite + React 18 + TypeScript + React Router v6 的前端，用于操作评测后台 `hi_api`：管理评测集、语料数据、执行评测、查看结果、修改配置、Excel 批量导入。

## 快速运行（PowerShell）

```powershell
cd hi_ui
npm install
npm run dev
```

访问: http://localhost:3000

已配置代理：所有以 `/api` 开头的请求自动转发到 `http://127.0.0.1:8000`（见 `vite.config.ts`）。

## 主要页面

| 页面 | 路径 | 功能 |
|------|------|------|
| 首页 | `/` | 简介 |
| 评测集 | `/sets` | 列表、创建、单集合执行、跳转结果 |
| 集合数据 | `/set/:id` | 列表、添加、单条执行、查看结果 |
| 集合结果 | `/results/set/:id` | 查看指定集合所有结果 |
| 数据结果 | `/results/data/:setId/:corpusId` | 查看某条数据的所有执行结果（使用 eval_set_id + corpus_id 唯一定位） |
| 多集合执行 | `/multi-execute` | 选择多个集合并行执行，支持全局并发上限 |
| 配置管理 | `/config` | 查看与更新后端的 URL / API KEY / hotline / userphone |
| Excel 导入 | `/upload` | 上传 Excel 文件批量导入评测数据 |

## 执行说明

1. 单条语料执行：在集合数据页面点击“执行”。
2. 单集合批量执行：在评测集列表点击某集合 “执行”。
3. 多集合执行：到“多评测集执行”选择集合后“开始执行”。
4. 执行完成后可在结果页面刷新查看 `答案 / 意图 / 分数 / KDB / agent_version / exec_time`。

## Excel 导入格式

表头需包含：`content`（语料）可选列：`expected`、`intent`。后端会解析并创建对应记录。重复内容策略由后端控制（当前假设允许重复）。

## 开发提示

如果需要新增字段，请同步更新：
1. `src/types/index.ts` 类型定义
2. 相关页面渲染逻辑
3. API 客户端 `src/api/client.ts`

## 运行前端自动化

需要我在当前工作区执行依赖安装并启动开发服务器，请回复：`运行前端`。

## 常见问题

1. 端口冲突：修改 `vite.config.ts` 中 `server.port`。
2. 后端未启动：所有请求会失败，请先运行 FastAPI 服务（默认 8000）。
3. CORS 问题：使用代理后应避免，若直接跨域访问需在后端允许来源。

欢迎继续提出新需求：例如结果筛选、导出、执行进度实时推送（WebSocket）等。

## 优化与变更文档

前端近期的 UI/UX 改进（骨架加载、可关闭错误横幅、基础样式）记录在 `doc/ui_optimizations.md`，包括代码片段与验证步骤，便于回顾与扩展。

注意：前端已迁移部分页面到 Ant Design 组件（`EvalSetsPage`）。在第一次运行前请确保安装依赖：

```powershell
cd hi_ui
npm install
```

启动 dev server 后，检查页面是否呈现 AntD 的样式（例如 Button、Table 样式和 Alert 图标）。

## Ant Design 迁移说明

部分页面已迁移至 Ant Design（AntD）以统一界面风格，并提高开发效率。主要变更包括：

- 使用 AntD 的 `Table`, `Form`, `Input`, `Button`, `Upload`, `Collapse`, `List` 等组件替换原生标签。
- 新增 `src/components/ErrorBanner.tsx` 用于统一错误提示（基于 AntD `Alert`）。
- 运行前务必安装依赖：`antd` 与 `@ant-design/icons`。

运行（PowerShell）：
```powershell
cd hi_ui
npm install
npm run dev
```

如果你想我继续：我可以完成剩余页面的样式统一（例如将 `details` -> `Collapse`、移除剩余的内联样式、统一按钮尺寸），或帮你在本地启动 dev server 并解决任何样式/类型问题。
