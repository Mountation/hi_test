# 后端接口文档

> 项目名称：hi_api  
> 基础路径：`/api/v1`（部分路由已在具体 router 中包含前缀）  
> 返回格式：JSON  
> 字符编码：UTF-8  
> 版本：0.1.0  
> 更新日期：2025-10-21

---
## 总览

| 模块 | 描述 | 主要路径前缀 |
|------|------|--------------|
| 评测集 EvalSet | 评测数据集合管理（创建、查询、删除、更新、Excel 导入） | `/api/v1/evalsets` |
| 评测数据 EvalData | 评测集中具体的语料及期望结果 | `/api/v1/evalsets/{eval_set_id}/data` |
| 评测结果 EvalResult | 执行评测后得到的结果、意图、评分等 | `/api/v1/evalresults` |
| 配置 Config | Agent 相关的基础配置查询与修改 | `/api/v1/config/test` |

---
## 通用说明
- 所有写操作（POST/PATCH/DELETE）在失败时返回标准的错误结构：`{"detail": "错误描述"}`。
- 删除操作为软删除（只标记 `deleted=true`），不会物理移除数据库记录。
- 时间字段为 ISO 8601 格式（例如：`2025-10-21T12:34:56.123Z`）。
- 分页暂未实现，列表接口返回全部未删除数据。

---
## 1. 评测集模块（EvalSet）
### 数据模型
```jsonc
EvalSet {
  id: number,
  name: string,
  count: number,        // 内含评测数据条目数量
  created_at: string,   // 创建时间
  updated_at: string,   // 更新时间
  deleted: boolean      // 软删除标记
}
```
### 创建评测集
- 方法：`POST /api/v1/evalsets/`
- 请求体：
```json
{
  "name": "家电售后评测"
}
```
- 返回：`EvalSet`
- 可能错误：`409`（重名时可自行扩展）、`400` 参数校验失败

### 列出评测集
- 方法：`GET /api/v1/evalsets/`
- 返回：`EvalSet[]`

### 获取单个评测集
- 方法：`GET /api/v1/evalsets/{id}`
- 返回：`EvalSet`
- 错误：`404` 不存在

### 更新评测集名称
- 方法：`PATCH /api/v1/evalsets/{id}`
- 请求体：
```json
{ "name": "新名称" }
```
- 返回：更新后的 `EvalSet`
- 错误：`404` 不存在

### 删除评测集（软删除）
- 方法：`DELETE /api/v1/evalsets/{id}`
- 返回：HTTP 204 无内容
- 错误：`404` 不存在

### Excel 上传导入评测数据
- 方法：`POST /api/v1/evalsets/upload`
- 表单：`file` (multipart/form-data, Excel 文件)
- Excel 约定：第一行表头忽略；后续行：第1列 `content`，第2列 `expected`，第3列 `intent`
- 返回：
```json
{
  "eval_set_id": 12,
  "created": 58 // 导入成功的行数
}
```
- 错误：文件格式异常、空文件、解析错误时部分行跳过

---
## 2. 评测数据模块（EvalData）
### 数据模型
```jsonc
EvalData {
  id: number,
  eval_set_id: number,
  content: string,      // 输入语料
  expected: string|null,// 期望结果
  intent: string|null,  // 期望意图（可选）
  deleted: boolean
}
```
### 按评测集列出数据
- 方法：`GET /api/v1/evalsets/{eval_set_id}/data`
- 返回：`EvalData[]`
- 错误：`404` 评测集不存在

### 获取单条评测数据
- 方法：`GET /api/v1/evalsets/{eval_set_id}/data/{data_id}`
- 返回：`EvalData`
- 错误：`404` 数据不存在或不属于该评测集

### 创建评测数据
- 方法：`POST /api/v1/evalsets/{eval_set_id}/data`
- 请求体：
```json
{
  "eval_set_id": 12,       // 可与路径不一致，后端以路径覆盖
  "content": "挂机空调 E4 报错怎么处理？",
  "expected": "告知用户室外机故障，安排上门维修。",
  "intent": "报修咨询"
}
```
- 返回：`EvalData`
- 错误：`404` 评测集不存在

### 删除评测数据（软删除）
- 方法：`DELETE /api/v1/evalsets/{eval_set_id}/data/{data_id}`
- 返回：HTTP 204 无内容
- 错误：`404` 数据不存在或不属于该评测集

---
## 3. 评测结果模块（EvalResult）
### 数据模型
```jsonc
EvalResult {
  id: number,
  eval_set_id: number,
  eval_data_id: number,
  actual_result: string|null, // AI 返回的实际回答
  actual_intent: string|null, // AI 识别出的实际意图
  score: number|null,         // 评分(0-100)
  agent_version: string|null, // Agent 版本或完整信息 JSON
  kdb: 0|1,                   // 是否命中知识库
  exec_time: string,          // 执行时间
  deleted: boolean
}
```
### 创建结果（手动）
- 方法：`POST /api/v1/evalresults/`
- 请求体：
```json
{
  "eval_set_id": 12,
  "eval_data_id": 108,
  "actual_result": "已为您登记报修，稍后工程师联系您。",
  "actual_intent": "报修登记",
  "score": 85,
  "agent_version": "v2.1.0",
  "kdb": 1
}
```
- 返回：`EvalResult`

### 按评测集列出结果
- 方法：`GET /api/v1/evalresults/byset/{eval_set_id}`
- 返回：`EvalResult[]`

### 按评测数据列出结果
- 方法：`GET /api/v1/evalresults/bydata/{eval_set_id}/{corpus_id}`
- 说明：按评测集内序号（corpus_id）查询结果。由于 `corpus_id` 在不同评测集中可能重复，建议同时提供 `eval_set_id` 以便唯一定位语料。
- 返回：`EvalResult[]`

### 获取单个结果
- 方法：`GET /api/v1/evalresults/{id}`
- 返回：`EvalResult`
- 错误：`404` 不存在

### 删除结果（软删除）
- 方法：`DELETE /api/v1/evalresults/{id}`
- 返回：`{"success": true}`
- 错误：`404` 不存在或已删除

### 执行评测（自动调用 AI 并评分）
- 方法：`POST /api/v1/evalresults/execute`
- 请求体：
```json
{
  "eval_data_id": 108,
  "agent_version": "v2.1.0" // 可选，传入则覆盖自动获取
}
```
- 处理流程：
  1. 根据 `eval_data_id` 读取语料与期望结果。
  2. 并发调用：`get_answer`（获取回答）、`get_intent`（获取意图）、`is_Kdb`（知识库命中）、`get_agent_info`（Agent 信息）。
  3. 使用评分服务（`score_answer` → 远程 `AIEval.eval_ai`）提取分数。
  4. 组装并保存结果到 `eval_results` 表。
- 返回：`EvalResult`
- 错误：`404` 评测数据不存在

---
## 4. 配置模块（Config）
### 查询配置
- 方法：`GET /api/v1/config/test`
- 返回：
```json
{
  "url": "http://agent-runtime.../v1/",
  "api_key": "app-xxxxx",
  "hotline": "43001",
  "userphone": "11111111111"
}
```

### 更新配置
- 方法：`PATCH /api/v1/config/test`
- 请求体（任意字段可选）：
```json
{
  "url": "http://new-agent/v1/",
  "api_key": "app-NEWKEY",
  "hotline": "43002",
  "userphone": "18888888888"
}
```
- 返回：
```json
{
  "url": "http://new-agent/v1/",
  "api_key": "app-NEWKEY",
  "hotline": "43002",
  "userphone": "18888888888",
  "updated": true,
  "path": "e:/AIEval/hi_test/hi_api/config/config.yaml"
}
```
- 说明：写入 `config.yaml` 并刷新内存缓存。

---
## 错误与状态码
| 状态码 | 说明 | 场景示例 |
|--------|------|----------|
| 200 | 成功 | 普通查询成功 |
| 201 | 已创建 | POST 创建成功（当前部分接口返回200） |
| 204 | 无内容 | 删除成功（评测集/评测数据） |
| 400 | 请求错误 | 参数缺失/类型不符（可扩展） |
| 404 | 未找到 | 资源不存在或已软删除 |
| 409 | 冲突 | 名称重复（可扩展） |
| 500 | 服务器错误 | 配置写入失败等 |

---
## 安全与认证
当前接口未强制加入鉴权中间件；若后续需要：
- 方案建议：在 `main.py` 中使用全局依赖或 APIRouter 级别的 `dependencies=[Depends(auth)]`。
- 可扩展 Header：`Authorization: Bearer <token>`。

---
## 未来扩展建议
| 功能 | 描述 |
|------|------|
| 分页与筛选 | 列表接口添加分页、关键字搜索、时间范围过滤 |
| 结果批量执行 | 一次提交多个 `eval_data_id` 并发执行，提高效率 |
| 评分策略优化 | 增加多维度评分：相关性、完整性、礼貌性等 |
| 执行队列 | 引入任务队列（如 Celery/Redis）支持海量异步评测 |
| 导出 | 结果导出为 CSV/Excel 以便分析 |
| 鉴权 | 接入统一认证，细化角色权限（只读/执行/配置修改） |
| 配置分组 | 支持多套 Agent 配置，用于 A/B 对比测试 |

---
## 附录：示例调用
### PowerShell 示例
```powershell
# 执行单条评测
Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/v1/evalresults/execute -Body (@{eval_data_id=108} | ConvertTo-Json) -ContentType "application/json"

# 创建评测集
Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/v1/evalsets/ -Body (@{name="售后评测"} | ConvertTo-Json) -ContentType "application/json"

# 上传 Excel
Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/v1/evalsets/upload -InFile .\dataset.xlsx -ContentType "multipart/form-data"

# 更新配置
Invoke-RestMethod -Method Patch -Uri http://localhost:8000/api/v1/config/test -Body (@{url="http://new-agent/v1/"} | ConvertTo-Json) -ContentType "application/json"
```

### cURL 示例
```bash
curl -X POST http://localhost:8000/api/v1/evalresults/execute \
  -H "Content-Type: application/json" \
  -d '{"eval_data_id":108}'
```

---
**文档生成时间：2025-10-21**
