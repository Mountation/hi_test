# 前端 API 客户端变动说明

日期：2025-10-22

概述

- 为了修复前端页面在加载评测集时出现的类型与网络错误，对 `hi_ui/src/api/client.ts` 做了以下改动：
  - 在 `request()` 中使用 `BASE` 前缀拼接完整 URL，方便开发时切换直接请求后端或使用 Vite 代理。
  - 对 `fetch` 的返回做了 `res.json() as Promise<T>` 强制断言，帮助 TypeScript 正确推断泛型返回类型。
  - 在 `request()` 中处理 HTTP 204 状态（No Content），返回 `undefined` 以避免 JSON 解析错误。
  - 为所有 API 方法显式指定返回类型（来自 `hi_ui/src/types`），例如 `getEvalSets: () => request<EvalSet[]>('/api/v1/evalsets/')`，让编译器不再把结果视为 `unknown`。

原因

- 原先前端在调用 `api.getEvalSets()` 时，TS 将返回视为 `unknown`，导致 `setSets(await api.getEvalSets())` 在编译或运行时发生类型不匹配问题，从而阻止正确渲染。
- 另外，网络层面的问题（CORS 或后端未启动）导致请求直接失败，这在浏览器侧表现为 `Failed to fetch`。

变更文件

- `hi_ui/src/api/client.ts` — 请求函数与 API 方法类型注解已更新。
- `hi_ui/src/pages/EvalSetsPage.tsx` — load() 增强（try/catch + alert），使网络错误可见。

如何验证

1. 在前端项目目录下重启 dev server：

```powershell
cd hi_ui
npm run dev
```

2. 在后端可达的情况下刷新前端页面。

3. 若页面仍报错：在浏览器控制台查看 Network 面板，捕获请求的请求头、响应头与错误信息，并将错误贴到该文档或直接发给维护者以便定位。

注意事项

- `res.json() as Promise<T>` 是一个便捷的断言，假设后端总是返回符合类型的 JSON。若后端经常返回与类型不匹配的内容，应增加运行时的响应校验（例如 zod 或 io-ts）。
- 在生产构建中请确保 API 路径正确（可能需要替换 `BASE` 为生产 API 地址）。
