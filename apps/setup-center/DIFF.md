# `apps/setup-center/` 功能差异备忘

**用途**：记录本目录内**当前工作区相对已提交版本**的功能向改动摘要，便于提交前自检与上游合并时对照。  
**与仓库根 `DIFF.md` 的关系**：根目录文件是「本地化 fork ↔ 上游 openakita」的长期对照清单；本文件聚焦 **setup-center 单包** 的**待提交/当前批次**说明，提交合并后应**删改过时条目或整节**，避免与根表重复堆砌。

**不写入**：纯品牌字符串替换、仅注释/空白、未纳入构建的本地日志/心跳等（如仓库根的 `logs/`、`data/*.heartbeat`）。

---

## 当前未提交批次（工作区快照）

**快照依据**（openakita-localized-sync / 提交前步骤）：在仓库根执行 `git status --short -- apps/setup-center/`、`git diff --stat -- apps/setup-center/`；无暂存区命中；本节仅列**当前仍相对于 HEAD 变更**的路径。

**简要分析**：本批次为**侧栏「工作台」导航 + 五子路由占位**，不涉及 Tauri 命令或 `src-tauri/` 未提交改动。后续将各 `workbench_*` 视图从 `WorkbenchPlaceholderView` 替换为真实业务组件时，优先改 `App.tsx` 中 `renderStepContent` 的 lazy 与分支，侧栏 `ViewId` 与 hash 可保持不变。

| 路径 | 功能摘要 |
|------|----------|
| `src/types.ts` | 扩展 `ViewId`：`workbench_products`、`workbench_tickets`、`workbench_meeting`、`workbench_sandbox`、`workbench_team` |
| `src/App.tsx` | 懒加载 `WorkbenchPlaceholderView`；`_HASH_TO_VIEW` 增加 `#/workbench-products` 等五条 hash；`renderStepContent` 内为上述五视图各返回占位页 |
| `src/components/Sidebar.tsx` | 在「状态」项下新增可折叠分组「工作台」（`NavGroupId.workbench`、`wbViews`、进入子路由时自动展开）；子项：产品/工单/会议/沙盒/团队；**代码沙盒**图标为 `IconTerminal`（非 `IconFileCode`） |
| `src/views/workbench/WorkbenchPlaceholderView.tsx` | **新增（未跟踪）**：工作台子页共用占位；`titleKey` + `workbench.placeholderHint` |
| `src/i18n/zh.json`、`src/i18n/en.json` | `sidebar.workbench`、`sidebar.workbenchProducts` 等子菜单文案；根键 `workbench.placeholderHint` |

**合并/同步提示**：上游若无「工作台」分组，合并 `Sidebar.tsx` / `App.tsx` / `types.ts` 时保留本批 `ViewId`、hash 表与 `wbViews` 逻辑；占位组件可整体替换为业务实现而不影响路由键名。

---

## 维护约定

1. **提交前**：用根目录 skill `openakita-localized-sync` 中的「提交前：setup-center DIFF 回写」步骤，对 `apps/setup-center/` 跑 `git diff` / `git diff --cached` / 未跟踪列表，更新上表「当前未提交批次」；无待提交改动时可删除该节或改为「（无）」。  
2. **合并进 main 后**：将已上线行为吸收进仓库根 `DIFF.md` 对应小节（若属于长期与上游差异），并精简本节重复描述。
