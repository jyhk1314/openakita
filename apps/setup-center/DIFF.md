# `setup-center` 目录差异说明（openakita_jyhk ↔ openakita）

**对比路径**：`openakita_jyhk/apps/setup-center` 为定制侧，`openakita/apps/setup-center` 为对照侧。  
**说明**：本文按「文件/目录」归纳**功能与迁移相关**差异；**不**单独展开「OpenAkita → Synapse」等纯品牌更名（此类变更会散落在 `package.json`、`tauri.conf.json`、`index.html`、`android` 字符串资源、`Cargo.toml` 等多处，需另做关键字审计）。

---

## 一、已梳理的定制改造点（与你列的 1–20 条对齐）

| # | 目录/文件 | 要点 |
|---|-----------|------|
| 1 | `public/` | 增加研发云取 token 演示视频（如 `devtoken.mp4`）、研发云 favicon（如 `iwhalecloud-favicon.ico`）。 |
| 2 | `src/assets/` | 系统/品牌相关图片调整：`logo.png` 与上游内容不一致；**新增** `logo_b.png`。`platform_logos/` 两侧均有大量 IM 图标；若你本地还有未提交的图标增量，以工作区为准。 |
| 3 | `src/components/rd-process/` | **仅 jyhk 存在**：工单/研发流程相关 UI（如 `RdProcessManagementView`、`RdProcessFlow`、`RdProcessTicketTable`、`processMockData`、样式等）。 |
| 4 | `src/components/team-manage/` | **仅 jyhk 存在**：团队总览视图（`TeamManagementView`、`SummaryMetrics`、`WaterfallFlow`、`PersonnelTable`、`AIChatBox`、mock 与样式等）。 |
| 5 | `src/components/rd-center/` | **仅 jyhk 存在**：研发中心视图（如 `RdCenterView.tsx`、`rdWorkOrderPaths.ts`）。 |
| 6 | `src/components/Sidebar.tsx` | 相对上游有改动：减少内网不可达的链接/请求，切到本地或内网可用资源（与 `localFetch`、平台层配合）。 |
| 7 | `src/components/WindowsTitleBar.tsx` | **仅 jyhk 存在**（或上游无对应实现）：标题栏高度与常规桌面应用对齐。 |
| 8 | `src/i18n/en.json`、`src/i18n/zh.json` | 文案与新增流程/视图中英对照。 |
| 9 | `src/platform/detect.ts` | Windows 等平台识别/校验逻辑增强。 |
| 10 | `src/App.tsx` | 引导安装流程扩展：如 iWhaleCloud 身份校验、Claude Code CLI 检测等。 |
| 11 | `src/constants.ts` | 中国区体验相关：体工商 slug、公司/提供商等常量。 |
| 12 | `src/icons.tsx` | 团队管理、新菜单等所需图标。 |
| 13 | `src/styles.css` | 新页面与布局相关样式。 |
| 14 | `src/hooks/useVersionCheck.ts` | 关闭或绕过公网版本检查逻辑，适配内网/离线场景。 |
| 15 | `src-tauri/icons/` | 应用图标资源替换/增补（含多套尺寸、`synapse/` 子目录、`icon_b`、`logo_b` 等）。 |
| 16 | `src-tauri/resources/` | **大块新增**：Claude Code 初始化目录 `claude-code-init/`（含 `.claude`、插件市场快照等）、Windows 下 `claude-code-releases/.../claude.exe`、`synapse-term/`（终端代理、psmux、lazygit、脚本与配置等）。 |
| 17 | `src-tauri/src/rd_terminal/` | **仅 jyhk 存在**：嵌入式终端模块（`mod.rs`、`pty_manager.rs`、`commands.rs`、`deps.rs`、`transcripts.rs` 等）。 |
| 18 | `src-tauri/src/main.rs` | 注册/桥接 `rd_terminal` 等 Tauri 命令与初始化逻辑。 |
| 19 | `src-tauri/video/` | 打包用视频资源（如 `devtoken.mp4`、`llmtoken.mp4`），与引导/说明一致。 |
| 20 | `src-tauri/windows/` | NSIS 安装脚本等（`installer.nsi`、`hooks.nsh`）与上游不一致，属 Windows 安装链配套改造。 |

---

## 二、补充检出（建议纳入迁移/合并清单）

### 2.1 仅 jyhk 侧新增（除上表已覆盖外）

- **`src/components/ToastContainer.tsx`**：全局 Toast 容器（若上游无等价组件，属 UI 基建）。
- **`src/views/im-shared.ts`**：IM 相关共享逻辑抽离（仅 jyhk 有该文件）。
- **`android/app/src/main/java/com/synapse/mobile/MainActivity.java`**：与上游 `com.openakita.mobile` 包路径不同（除品牌外，注意包名/清单与 Capacitor 配置一致）。
- **`dist-web/`**、**`tsconfig.tsbuildinfo`**：构建产物；通常应 **`.gitignore`**，不宜作为「功能迁移」依赖项跟踪（若需对齐 CI，在脚本中生成即可）。

### 2.2 相对上游有改动的关键文件（同名不同内容）

以下与「内网化、本地 API、认证、日志、WebSocket」等强相关，**不限于** `detect.ts`：

- **平台层**：`src/platform/auth.ts`、`logger.ts`、`servers.ts`、`websocket.ts`、`index.ts`（及你已列的 `detect.ts`）。
- **网络入口**：`src/localFetch.ts`、`src/providers.ts`（与 Sidebar/常量/环境字段联动）。
- **壳与路由**：`src/main.tsx`、`src/components/Topbar.tsx`、`src/components/CliManager.tsx`、`src/components/OrgInboxSidebar.tsx`、`src/components/EnvFields.tsx`、`src/components/WebPasswordManager.tsx`、`src/components/ProviderSearchSelect.tsx`、`src/components/SearchSelect.tsx`、`src/components/TroubleshootPanel.tsx`、`src/components/PosterGenerator.tsx`、`src/components/ConfirmDialog.tsx` 等。
- **类型与主题**：`src/types.ts`、`src/theme.ts`、`src/boot.css`、`src/utils.ts`、`src/utils/clipboard.ts`、`src/hooks/useNotifications.ts`。
- **业务视图（节选）**：`src/views/ChatView.tsx`、`LoginView.tsx`、`AgentDashboardView.tsx`、`AgentManagerView.tsx`、`AgentSystemView.tsx`、`AgentStoreView.tsx`、`IMView.tsx`、`IMConfigView.tsx`、`IdentityView.tsx`、`MCPView.tsx`、`MemoryView.tsx`、`OrgEditorView.tsx`、`SchedulerView.tsx`、`ServerManagerView.tsx`、`SkillManager.tsx`、`SkillStoreView.tsx`、`TokenStatsView.tsx` 等（具体 diff 需按文件查看，多与端点/权限/文案有关）。

### 2.3 工程与打包配置（除品牌外的行为差异）

- **前端**：`package.json`、`package-lock.json`、`vite.config.ts`、`tsconfig.json`、`capacitor.config.ts`、`index.html`、`public/manifest.json`、`public/sw.js`。
- **Tauri / Rust**：`src-tauri/Cargo.toml`、`Cargo.lock`、`tauri.conf.json`、`build.rs`、`capabilities/default.json`、`Entitlements.plist`。
- **文档**：`README.md`、`AGENTS.md`（若含环境说明，可能与内网部署一致）。

### 2.4 上游 openakita 有、jyhk 当前目录中**不存在**的块（结构差异）

> 下列为「整目录/整文件仅在上游出现」，合并代码时需明确是**有意裁剪**还是**待移植**。**不是**品牌更名问题。

- **`src/api.ts`**：上游独立 API 封装；jyhk 侧可能已迁到 `localFetch` / 平台层。
- **组件**：`ErrorBoundary`、`FeishuQRModal`、`QQBotQRModal`、`WechatQRModal`、`WecomQRModal`、`PluginOnboardModal`、`OrgChatPanel`、`OrgDashboard`、`OrgProjectBoard`、`MemoryGraph3D`、`ModalOverlay`、`PanelShell`、`Section` 等。
- **大模块目录**：`src/components/org-editor/`（组织画布编辑器全套）、`src/components/pixel-office/`、`src/components/pixel-avatar/`、`src/components/ui/`（shadcn 风格 UI 套件）。
- **样式与工具**：`src/globals.css`、`src/styles/pet.css`、`src/lib/utils.ts`、`src/streamEvents.ts`。
- **Hooks**：`src/hooks/useEnvManager.ts`、`src/hooks/usePerfMode.ts`。
- **视图与子系统**：`src/views/PetView.tsx`、`PixelOfficeView.tsx`、`AdvancedView.tsx`、`FeedbackModal.tsx`、`LLMView.tsx`、`PluginManagerView.tsx`、`SecurityView.tsx`、`StatusView.tsx`，以及 **`src/views/chat/`** 下整棵聊天子树（组件、hooks、utils）。

---

## 三、统计参考（便于扫尾）

- 在排除 `node_modules`、`dist`、`target`、`gen` 前提下，两侧**内容不同**的同名文件约 **125** 个；**仅 jyhk** 侧多出的条目中，大量集中在 `src-tauri/resources/claude-code-init/`（宜在文档中按「整包资源」描述，不必逐文件罗列）。
- 若需要生成「逐文件清单」供 CI 校验，可用目录哈希对比脚本输出 CSV；本文件以**可读的迁移维度**归纳为主。

---

*生成说明：基于两目录递归比对（SHA256）与工作区抽样核对；若你后续将 `dist-web` 等移出版本库，请以 `.gitignore` 后的树为准重新扫一遍。*
