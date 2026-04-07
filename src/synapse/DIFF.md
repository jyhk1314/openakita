# `openakita/src/openakita` 与 `openakita_jyhk/src/synapse` 功能差异（按文件）

对比方式：目录结构一致（458 个文件一一对应），以下**不视为功能差异**单独展开：包名/导入路径 `openakita`↔`synapse`、产品名文案、`OPENAKITA_*`↔`SYNAPSE_*` 环境变量、`requires.openakita`↔`requires.synapse`、插件清单键名、`metadata.openakita`↔`metadata.synapse`、健康检查 JSON 字段 `openakitaVersion`↔`synapseVersion` 等**品牌与命名迁移**。

---

## 一、仅存在于 jyhk（synapse）的文件

| 文件 | 说明 |
|------|------|
| `api/routes/yuque.py` | 语雀知识库 HTTP API：创建/删除知识库、文档 CRUD、搜索等，供前端与自动化调用。 |
| `api/routes/gitnexus.py` | GitNexus 代理：`POST /api/gitnexus/query` 等，将前端请求转为后端 MCP `tools/call`（JSON-RPC），同步等待结果。 |
| `api/routes/dev_iwhalecloud.py` | 研发云（`dev.iwhalecloud.com`）集成：需求/缺陷等环节、Playwright 登录与业务 API 等（体量较大）。 |

---

## 二、API 与 HTTP 层

| 文件 | 功能差异摘要 |
|------|----------------|
| `api/server.py` | 在 `create_app` 中 **挂载** `yuque`、`gitnexus`、`dev_iwhalecloud` 三路 `APIRouter`；并增加 `access_logger`（`/api` 访问日志）等与 upstream 不同的观测/运维向改动。 |
| `api/schemas.py` | 增加 **`success_response` / `error_response`**（`errorcode` + `message` + `data` 结构），供语雀/GitNexus 等路由统一返回格式。 |
| `api/auth.py` | 增加 **`base64url` 编解码**及一套 **`_jwt_encode` / `_jwt_decode`（HS256，stdlib）**；当前 **`create_access_token` 仍使用 `core.auth.tokens` 的 `encode_jwt`**，上述 JWT 辅助函数在文件内**未被调用**，属于并行/预留实现。 |

---

## 三、Agent 与浏览器自动化

| 文件 | 功能差异摘要 |
|------|----------------|
| `agents/orchestrator.py` | 子 Agent 使用 **隔离浏览器**（`isolated_browser`）时，upstream 会 `import BrowserUseRunner` 并设置 **`agent.bu_runner`**；jyhk 侧 **注释掉 BrowserUseRunner 与 `bu_runner`**，仅替换 `browser_manager` 与 `pw_tools`。效果：隔离子 Agent **不再挂载 browser-use 运行器**（与 `browser_task`/browser-use 能力解耦）。 |

---

## 四、工具定义与 `setup` 包（已重新核对）

对以下文件做 **`synapse` / `Synapse` → `openakita` / `OpenAkita` 归一化** 后与 upstream **逐字一致**，**无功能差异**（仅 jyhk 侧模块 docstring 仍写「Synapse」）：

- `tools/definitions/base.py`（含 `ToolCategory`、`CATEGORY_PREFIXES` 等与 upstream 对齐）
- `tools/definitions/browser.py`（`BROWSER_TOOLS` 列表与 upstream 对齐，**无**单独的 `browser_task` 定义差异）
- `setup/__init__.py`（均为 `SetupWizard` 的 `__getattr__` 懒加载，与 upstream 相同）

---

## 五、LLM 提供商注册表

| 文件 | 功能差异摘要 |
|------|----------------|
| `llm/registries/providers.json` | jyhk **在列表首部增加** `"WhaleCloud (公司)"` / `slug: iwhalecloud`（默认 `lab.iwhalecloud.com/gpt-proxy`、环境变量建议 `IWHALECLOUD_API_KEY` 等），用于公司内部代理。 |

---

## 六、其他零散差异（非命名迁移）

| 文件 | 功能差异摘要 |
|------|----------------|
| `tools/handlers/web_fetch.py` | 注释/文档中的 GitHub 示例链接指向 **fork**（如 `jyhk1314/openakita`），与 upstream 官方仓库 URL 不同。 |
| `tools/subprocess_bridge.py` | 注释中补充 **打包场景下除 playwright 外还可能涉及 `browser_use`**。 |
| `tools/desktop/vision/analyzer.py` | 增加简短中文注释（如 base64 转换说明），逻辑需与 upstream 逐段对照确认无行为变化。 |

---

## 七、无行为意义或仅格式/空行的差异（知悉即可）

以下在归一化包名后仍有文本差异，多为 **尾随空行、切片空格 `[:] ` vs `[:]`、logger 单行/多行、f-string 换行、测试临时文件名** 等，一般不改变业务逻辑：

- `__init__.py`（`__all__` 表示空项的写法）
- `core/im_context.py`、`evolution/*.py`、`hub/*.py`、`llm/converters/messages.py`、`mcp_servers/web_search.py`、`python_compat.py`、`runtime_env.py`
- `llm/registries/deepseek.py`、`kimi.py`、`minimax.py`（多为文件首/尾空行）
- `tools/browser/manager.py`、`playwright_tools.py`、`webmcp.py`，`tools/desktop/actions/*.py`、`capture.py`、`uia/*.py`
- `sessions/session.py`、`tools/sticker.py`、`testing/cases/tools/shell_tests.py`、`tracing/tracer.py`

若需 **严格证明** 上述文件零行为差异，可对单文件做 `ast` 比对或运行相关单测。

---

## 八、自动化比对备忘

曾用「`synapse`→`openakita` 字符串归一化」后全文比对：约 **41** 个文件仍有文本不同；其中多数可归入**命名迁移**或**第七节**的噪声。本文件按**功能影响**做了人工归纳，**不以行数统计为准**。
