# 工作区改造点摘要（相对 `origin/main`）

> 生成依据：当前分支相对远程 `main` 的 **已跟踪文件变更**（`git diff`）与 **未跟踪新增**（`git status`）。  
> 关联方案：[`2026-03-26-rd-center-synapse-term-migration.md`](./2026-03-26-rd-center-synapse-term-migration.md)（研发中心 / SynapseTerm 迁入 Setup Center）。

---

## 1. 变更规模一览

| 类别 | 说明 |
|------|------|
| 已修改 / 删除（跟踪） | **28** 个路径；约 **+2906 / -1005** 行（含生成 schema、lockfile） |
| 未跟踪（新增） | `rd_terminal` 模块、`RdCenterView.tsx`、`resources/` 下大量内容、`devtoken.mp4` / `llmtoken.mp4` 等；**提交前需确认体积与 `.gitignore` 策略** |

**主要区域**：`apps/setup-center`（前端 + Tauri）、Python API（移除 KAG）、根目录 `requirements.txt` 与 `.gitignore`。

---

## 2. 研发中心（Setup Center）— 与方案文档的对应

本节对应迁移方案中的 **F1（React + xterm）**、**R1（`resources/synapse-term/`）**、**Rust 模块拆分**、**Windows + Tauri 门控**。

### 2.1 前端

| 改造点 | 路径 / 说明 |
|--------|-------------|
| 新视图与工单 TAB | `RdCenterView.tsx`（未跟踪）：`@xterm/xterm` + `@xterm/addon-fit`，Ant Design `Tabs`，**MOCK 工单列表**（与方案「首版 MOCK、登录后异步加载」一致） |
| 工单路径与会话名 | `rdWorkOrderPaths.ts`（未跟踪）：`~/.synapse/work/<工单ID>` 与 `synapse-work-<sanitized>`，与 Rust `transcripts` 侧 sanitize 对齐 |
| 侧栏入口 | `Sidebar.tsx`：`ViewId` 增加 `rd_center`，`rdCenterVisible` 控制显示 |
| 主壳集成 | `App.tsx`：`view === "rd_center"` 分支、`content--rdFlexFill` 布局、`rdCenterVisible={IS_TAURI && IS_WINDOWS}` |
| 平台探测 | `platform/detect.ts`、`platform/index.ts`：导出 `IS_WINDOWS`（UA 判断），供研发中心门控 |
| 引导 / 根组件 | `main.tsx`：与窗口标题栏、研发中心相关的挂载调整（见同 diff） |
| Windows 标题栏 | `WindowsTitleBar.tsx`（未跟踪）：桌面窗口装饰相关 |
| 样式 | `styles.css`、`boot.css`：研发中心终端与布局类名（如 `rdCenter*`） |
| i18n | `i18n/zh.json`、`i18n/en.json`：`sidebar.rdCenter`、`rdCenter.*` 等文案 |
| 依赖 | `package.json` / `package-lock.json`：新增 `@xterm/xterm`、`@xterm/addon-fit` |

### 2.2 Tauri Rust

| 改造点 | 路径 / 说明 |
|--------|-------------|
| 终端子系统模块 | `src-tauri/src/rd_terminal/`（未跟踪）：`mod.rs`、`pty_manager.rs`、`commands.rs`、`deps.rs`、`transcripts.rs` |
| 接入主程序 | `main.rs`：`mod rd_terminal;`、`.manage(PtyManager::new())`、注册一组 `invoke`（如 `pty_create_attach`、`pty_write`、`create_agent_workspace`、`transcripts_*`、`agent_*` 等），退出时 `kill_psmux` 相关逻辑 |
| 依赖 | `Cargo.toml`：`portable-pty`、`tokio`（等与 PTY/异步相关的 crate）；`Cargo.lock` 同步 |
| 能力与 schema | `capabilities/default.json`：增加 `shell:allow-open` 等；`gen/schemas/*.json` 为生成物 |
| 打包资源 | `tauri.conf.json`：`bundle.resources` 增加 `resources/claude-code-releases/`、`resources/synapse-term/`、`video/` |
| 构建脚本 | `build.rs`：`rerun-if-changed` 覆盖 `synapse-term`、`video`、`claude-code-releases`；`ensure_claude_bundle_from_repo` 从仓库根 `resources/claude-code-releases/` 同步到 `src-tauri/resources/`；`strip_nested_git_dirs_under_claude_code_init` 避免 Windows 打包读嵌套 `.git` 失败 |

### 2.3 资源目录（`src-tauri/resources`）

- **已纳入跟踪的改造**：`.gitignore` 增加对 `resources/claude-code-releases/*` 的忽略（保留 `.gitkeep` 模式，与 `synapse-server` 类似）。
- **未跟踪内容**：除方案所述 `synapse-term` 外，工作区还存在大量 `claude-code-init` 等树；**当前跟踪到的 `resources/synapse-term/` 至少包含**：`psmux.exe`、`lazygit.exe`、`agent-workspace.ps1`、`synapse-term-agent-tmux.conf`、`README.md`。  
- **方案中的 `ps7/`、tmux zip 等**：若本地未出现，需按 `synapse-term/README.md` 自行放置后再打包验证。

### 2.4 媒体资源调整

- **删除**：`apps/setup-center/public/token.mp4`、`src-tauri/video/token.mp4`（大文件从仓库移除或替换策略）。
- **新增（未跟踪）**：`public/devtoken.mp4`、`src-tauri/video/devtoken.mp4`、`src-tauri/video/llmtoken.mp4` — 需在 PR 中说明用途及是否长期入库（体积与许可证）。

---

## 3. Python 后端：KAG 路由移除

| 改造点 | 说明 |
|--------|------|
| 删除路由模块 | `src/synapse/api/routes/kag.py` 整文件删除 |
| 取消挂载 | `server.py`：移除 `kag` 的 import 与 `app.include_router(kag.router, tags=["KAG知识库"])` |
| 依赖 | `requirements.txt`：移除 `openspg-kag>=0.8.0`（Dev 可选区） |

**影响**：HTTP API 不再暴露原 KAG 知识库相关接口；若仍有文档或客户端硬编码该路径，需同步清理或改指向其他服务。

---

## 4. 其他小项

- **`constants.ts`**：与 bundled Claude Code 版本等常量对齐（如 `CLAUDE_CODE_BUNDLED_VERSION`，与 `main.rs` 路径约定一致）。
- **LF/CRLF**：Windows 下 Git 对若干文件提示「下次触碰将转 CRLF」，合并时注意团队统一 `core.autocrlf` 策略，避免无意义整文件 diff。

---

## 5. 提交与评审建议（Checklist）

1. [ ] 将**应入库**的未跟踪源码与配置纳入 `git add`（`rd_terminal`、`RdCenterView.tsx`、`rdWorkOrderPaths.ts`、`WindowsTitleBar.tsx` 等）。
2. [ ] 大体积二进制（`ps7`、`tmux` zip、视频 mp4、`claude-code-init` 子树）按仓库策略：**要么 LFS/制品库，要么文档说明本地放置**，避免误提交。
3. [ ] 本地执行 `npm run build` / `cargo check` / `tauri build`（Windows）验证 `resources/synapse-term` 与 PTY 全链路。
4. [ ] 确认删除 KAG 后无其他模块仍 `import` `kag` 或依赖 `openspg-kag`（可全库检索 `kag`、`openspg`）。
5. [ ] 与方案文档核对：**仅 Windows + Tauri 显示研发中心**、工单 MOCK、默认工作区路径等是否已在 UI 与 Rust 侧一致实现。

---

## 6. 文档关系

| 文档 | 角色 |
|------|------|
| [`2026-03-26-rd-center-synapse-term-migration.md`](./2026-03-26-rd-center-synapse-term-migration.md) | 目标架构与阶段划分（评审稿） |
| **本文** | 当前工作区相对 `main` 的**实际改动清单**与合入注意事项 |

---

*文档版本：2026-03-27 — 随工作区演进可更新「未跟踪」与验收勾选状态。*
