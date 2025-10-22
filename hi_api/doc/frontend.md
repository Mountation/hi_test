# 前端脚手架说明

日期：2025-10-22

概述

- 前端 `hi_ui` 使用 Vite + React + TypeScript 搭建完成。
- 已创建 API 客户端模块和页面骨架（EvalSetsPage、EvalDataPage、结果页面、配置页面）。
- 已将 Ant Design 与 Pro 组件相关依赖添加到 `package.json`，但尚未执行安装。

关注文件

- `hi_ui/package.json` — 包含 `antd`、`@ant-design/pro-components`、`dayjs` 等依赖。
- `hi_ui/src/pages/*` — TypeScript React 页面；由于 API 返回类型为 `unknown`，存在部分类型错误。

当前状态

- 前端骨架已完成；仍需解决类型错误（安装类型定义或修正 API 客户端返回类型）。
- 后续计划：安装 UI 依赖、将页面重构为 Ant Design Pro 布局并设定主题。

如何继续

1. 进入 `hi_ui` 执行依赖安装：

```powershell
cd hi_ui
npm install
```

2. 修复 TypeScript 中的 `unknown` 问题：确保 API 客户端返回已声明的类型（或在客户端做类型断言/校验）。
3. 使用 Ant Design 组件替换页面中的原生 HTML 以提升一致性与视觉效果。

备注

- 如需，我可以为你在工作区中执行依赖安装并把页面重构为 Pro 组件。
