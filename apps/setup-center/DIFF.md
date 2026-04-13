# `apps/setup-center/` 功能差异备忘

**用途**：记录本目录内**当前工作区相对已提交版本**的功能向改动摘要，便于提交前自检与上游合并时对照。  
**与仓库根 `DIFF.md` 的关系**：根目录文件是「本地化 fork ↔ 上游 openakita」的长期对照清单；本文件聚焦 **setup-center 单包** 的**待提交/当前批次**说明，提交合并后应**删改过时条目或整节**，避免与根表重复堆砌。

**不写入**：纯品牌字符串替换、仅注释/空白、未纳入构建的本地日志/心跳等（如仓库根的 `logs/`、`data/*.heartbeat`）。

---

## 当前未提交批次（工作区快照）

**快照依据**（openakita-localized-sync / 提交前步骤）：在仓库根执行 `git status --short -- apps/setup-center/`、`git diff --stat -- apps/setup-center/`；本节列出**产品公共服务引导及工作台产品管理视图**相关的新增与改动。

**简要分析**：本批次主要为**初始化引导增加「产品公共服务」配置步骤**，以及**在工作台实现「产品管理」功能组件**。包括探测 10001~13011 系列端口连通性并将 IP 写入 `devservice.ip`，支持获取并配置产品/仓库/分析状态。此外，修复了 Claude Code 和 OpenCode 一键配置在配置已存在时的跳过逻辑。

| 路径 | 功能摘要 |
|------|----------|
| `src-tauri/src/main.rs` | 增加 `devservice.ip` 读写及 `probe_devservice_ports` 连通性探测命令；优化 `claude_code_apply_user_init` 使配置文件存在时不覆盖 |
| `src/App.tsx` | 新增引导步骤 `ob-devservices`（探测 IP 端口并保存）；工作台视图懒加载接入 `ProductManagerView`；修复 Claude 一键配置的成功/错误状态及重试逻辑 |
| `src/api/rdUnifiedService.ts` | **新增（未跟踪）**：封装获取/保存产品、获取分析过程、更新仓库信息的后端接口调用 |
| `src/components/product/` | **新增（未跟踪）**：`ProductManager`（产品主列表）、`ProductCard`（产品卡片）、`ProductModal`（产品编辑弹窗）、`ProductDetail`（详情与各类图谱分析入口）、`RepoUpdateDialog`（更新仓库对话框）及相关类型与样式 |
| `src/views/workbench/ProductManagerView.tsx` | **新增（未跟踪）**：包装 `ProductManager` 并在其中注入后端 API 基址 |
| `src/i18n/` (`en.json`, `zh.json`) | 新增 `ob-devservices` 引导文案及 `workbench.products` 系列产品管理视图中英文化文案；新增色弱与高对比主题文案 |
| `src/platform/index.ts` | 补充导出 `IS_WINDOWS` 平台检测变量 |
| `src/styles.css` | 优化侧边栏折叠后的图标居中、隐藏缩进与装饰线，增加部分换行样式 |

**合并/同步提示**：此批次属于典型的**本地个性化需求（业务化改造）**。与上游合并时需重点保护 `App.tsx` 中的引导步骤顺序和组件注入，以及产品工作台的所有新文件，上游对应模块若有重构应避免覆盖这些本地业务逻辑。

---

## 维护约定

1. **提交前**：用根目录 skill `openakita-localized-sync` 中的「提交前：setup-center DIFF 回写」步骤，对 `apps/setup-center/` 跑 `git diff` / `git diff --cached` / 未跟踪列表，更新上表「当前未提交批次」；无待提交改动时可删除该节或改为「（无）」。  
2. **合并进 main 后**：将已上线行为吸收进仓库根 `DIFF.md` 对应小节（若属于长期与上游差异），并精简本节重复描述。