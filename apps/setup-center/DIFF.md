# `apps/setup-center/` 功能差异备忘

**用途**：记录本目录内**当前工作区相对已提交版本**的功能向改动摘要，便于提交前自检与上游合并时对照。  
**与仓库根 `DIFF.md` 的关系**：根目录文件是「本地化 fork ↔ 上游 openakita」的长期对照清单；本文件聚焦 **setup-center 单包** 的**待提交/当前批次**说明，提交合并后应**删改过时条目或整节**，避免与根表重复堆砌。

**不写入**：纯品牌字符串替换、仅注释/空白、未纳入构建的本地日志/心跳等（如仓库根的 `logs/`、`data/*.heartbeat`）。

---

## 当前未提交批次（工作区快照）

**快照说明**：以下依据 `git status` / `git diff`（未暂存）整理；含未跟踪的功能性路径时仅作索引，不展开二进制内容。

| 路径 | 功能摘要 |
|------|----------|
| `src-tauri/resources/opencode-releases/` | 新增打包资源目录（含 `opencode-windows-x64.zip`），供离线安装 OpenCode |
| `src-tauri/tauri.conf.json` | `bundle.resources` 增加 `resources/opencode-releases/` |
| `src-tauri/src/main.rs` | 引导阶段 **研发工具** 能力：统一 `dev_tools_check`（Claude Code / Cursor CLI / OpenCode 三者任一为真即可继续）；`bundled_claude_win32_dir` 简化为 `resources` + `CARGO_MANIFEST_DIR` 回退；新增 `bundled_opencode_windows_zip_path`、`synapse_opencode_install_dir`、`extract_zip_safely_to_dir`、`write_windows_cmd_shim`；`claude_code_install_local_sync` + `opencode_cli_install_local_sync` 离线复制/解压至工作区并写 `bin/*.cmd`、合并用户 PATH；安装日志事件统一为 `dev_tools_install_log`；**移除** `claude_code_check` 单点接口与 **winget** 安装路径；注册 Tauri 命令 `dev_tools_check`、`claude_code_install`、`opencode_cli_install` |
| `src/App.tsx` | 引导页「CLI」步骤改为多工具列表 UI：调用 `dev_tools_check`；Claude / OpenCode 一键安装分别走 `claude_code_install`、`opencode_cli_install`；监听 `dev_tools_install_log`；移除 `CLAUDE_CODE_BUNDLED_VERSION` 与 winget/脚本多入口安装格 |
| `src/i18n/en.json`、`src/i18n/zh.json` | `onboarding.step` 补全；`onboarding.claudeCode` 文案改为「研发工具 / Dev tools」语义，覆盖三工具说明、安装提示与错误提示 |
| `src/styles.css` | 新增 `.obDevToolOptList`、`.obDevToolOptRow` 布局样式 |

**合并/同步提示**：上游若仍只有「仅 Claude Code」检测，合并 `main.rs` / `App.tsx` 时需保留本批 **`dev_tools_check` 聚合模型** 与 **OpenCode zip 离线安装** 分支；`tauri.conf.json` 需保留 `opencode-releases` 资源声明。

---

## 维护约定

1. **提交前**：用根目录 skill `openakita-localized-sync` 中的「提交前：setup-center DIFF 回写」步骤，对 `apps/setup-center/` 跑 `git diff` / `git diff --cached` / 未跟踪列表，更新上表「当前未提交批次」；无待提交改动时可删除该节或改为「（无）」。  
2. **合并进 main 后**：将已上线行为吸收进仓库根 `DIFF.md` 对应小节（若属于长期与上游差异），并精简本节重复描述。
