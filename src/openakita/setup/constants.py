# 总步骤数
_TOTAL_STEPS = 11

# 每个步骤的关键信息
_STEP_KEYS = {
    "1": {"zh": "检查环境", "en": "Checking Environment"},
    "2": {"zh": "语言 & 地区", "en": "Language & Region"},
    "3": {"zh": "创建目录结构", "en": "Creating Directory Structure"},
    "4": {"zh": "配置 LLM 端点", "en": "Configure LLM Endpoints"},
    "5": {"zh": "配置提示编译模型 (可选)", "en": "Configure Prompt Compiler Model (Optional)"},
    "6": {"zh": "配置 IM 通道 (可选)", "en": "Configure IM Channels (Optional)"},
    "7": {"zh": "配置记忆系统", "en": "Configure Memory System"},
    "8": {"zh": "语音识别 (可选)", "en": "Voice Recognition (Optional)"},
    "9": {"zh": "高级配置 (可选)", "en": "Advanced Configuration (Optional)"},
    "10": {"zh": "保存配置", "en": "Saving Configuration"},
    "11": {"zh": "测试连接", "en": "Testing Connection"},
}

# 中国区提供商 slug 列表
_CHINA_SLUGS = {
    "dashscope", "kimi-cn", "minimax-cn", "siliconflow",
    "volcengine", "zhipu-cn", "qianfan", "hunyuan", "yunwu",
    "longcat", "iflow",
}

# 公司内部提供商
_WHALECLOUD_SLUGS = {
    "iwhalecloud"
}

# 交互信息
_WELCOME_TITLE = {"zh": "欢迎使用 Synapse", "en": "Welcome to Synapse"}

_WELCOME_TEXT = {
"zh": """
# 欢迎使用 Synapse

**你的忠诚可靠的 AI 研发助手**

本向导将引导你在几步内完成 Synapse 的配置：

1. 配置 LLM API
2. 配置 IM 通道（可选：钉钉、企业微信、QQ 官方机器人、OneBot 等）
3. 配置记忆系统
4. 测试连接

随时按 Ctrl+C 可取消。
""",   
"en": """
# Welcome to Synapse

**Your Loyal and Reliable AI Development Assistant**

This wizard will help you set up Synapse in a few simple steps:

1. Configure LLM API (Claude, OpenAI-compatible, etc.)
2. Set up IM channels (optional: DingTalk, WeCom, QQ Official Bot, OneBot, etc.)
3. Configure memory system
4. Test connection

Press Ctrl+C at any time to cancel.
"""}

_AGREEMENT_TITLE = {"zh": "使用风险须知", "en": "Risk Acknowledgment"}

_AGREEMENT_TEXT = {"zh": """
## 使用风险须知

Synapse 是一款基于大语言模型（LLM）驱动的 AI Agent 软件。
在使用前，你需要了解并接受以下事项：

**1. 行为不可完全预测**
AI Agent 的行为受底层大语言模型驱动，其输出具有概率性和不确定性。
即使在相同输入下，Agent 也可能产生不同的行为结果，包括但不限于：
执行非预期的文件操作、发送非预期的消息、调用非预期的工具等。

**2. 使用过程必须监督**
你有责任在使用过程中保持对 AI Agent 行为的监督。对于需要审批的
工具调用（如文件删除、系统命令执行、消息发送等），请在确认操作
内容合理后再批准执行。强烈建议不要在无人监督的情况下开启自动
确认模式（AUTO_CONFIRM）。

**3. 可能造成的风险**
AI Agent 在执行任务时可能导致：
- 数据丢失或损坏（如误删文件、覆盖重要数据）
- 发送不当消息（如通过 IM 通道发送错误内容）
- 执行危险系统命令
- 产生非预期的 API 调用和费用消耗
- 其他无法预见的副作用

**4. 免责声明**
Synapse 按「现状」(AS IS) 提供，不附带任何形式的明示或暗示
担保。项目维护者和贡献者不对因使用本软件而产生的任何直接、间接、
偶然、特殊或后果性损害承担责任。你应当自行承担使用本软件的全部
风险。

**5. 数据安全**
你的对话内容、配置信息和工具调用记录可能被发送至第三方 LLM 服务
商。请勿在对话中提供敏感的个人信息、密码、密钥等机密数据，除非
你充分了解并接受相关风险。
""", "en": """
## Risk Acknowledgment

Synapse is an AI Agent software powered by large language models (LLMs).
Before using, you need to understand and accept the following:

**1. Behavior is not fully predictable**
The AI Agent's behavior is driven by underlying LLMs, whose outputs are
probabilistic and non-deterministic. Even with identical inputs, the Agent
may produce different results, including but not limited to: unintended file
operations, unintended messages, and unintended tool invocations.

**2. Supervision is required**
You are responsible for supervising the AI Agent's actions during use. For
tool calls that require approval (e.g. file deletion, system commands,
sending messages), please confirm that the operation is reasonable before
approving. It is strongly recommended not to enable auto-confirm (AUTO_CONFIRM)
without active supervision.

**3. Potential risks**
The AI Agent may, while performing tasks, cause:
- Data loss or corruption (e.g. accidental file deletion, overwriting important data)
- Inappropriate messages (e.g. sending wrong content via IM channels)
- Execution of dangerous system commands
- Unintended API calls and cost consumption
- Other unforeseeable side effects

**4. Disclaimer**
Synapse is provided "AS IS" without any express or implied warranty. The
maintainers and contributors are not liable for any direct, indirect,
incidental, special or consequential damages arising from use of this
software. You assume all risks of using this software.

**5. Data security**
Your conversations, configuration and tool-call records may be sent to
third-party LLM providers. Do not share sensitive personal information,
passwords, keys or other confidential data in conversations unless you
fully understand and accept the associated risks.
"""}

_CONFIRM_PHRASE_ZH = "我已知晓"
_CONFIRM_PHRASE_EN = "I ACKNOWLEDGE"

_CHOOSE_LOCALE_TEXT = {"zh": "此选项会影响模型下载、语音识别等默认设置。", "en": "This affects default settings for model downloads, voice recognition, etc."}
_CHOOSE_LLM_OPTIONS = {"zh": "选择 LLM 提供商", "en": "Select LLM Provider:"}