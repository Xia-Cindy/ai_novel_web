import json
from typing import Dict

from .analyzer import summarize_reference


def build_world_prompt(style_json: Dict, user_setting: Dict, reference_text: str = "") -> str:
    return f"""【生成目标】WORLD
你是小说世界构建器。

必须严格模仿以下写作风格：

【风格规则】
{_json(style_json)}

【参考文本摘要】
{summarize_reference(reference_text)}

【用户设定】
灵感：{user_setting.get("inspiration", "")}
题材：{user_setting.get("genre", "")}
地点：{user_setting.get("location", "")}
背景：{user_setting.get("background", "")}
人物设定：{user_setting.get("characters", "")}
文风模块：{user_setting.get("writing_style", "")}
模板模块：{user_setting.get("template", "")}
公有库逻辑：{user_setting.get("public_library", "")}

请生成：

1. 世界观设定
2. 核心冲突
3. 势力结构
4. 主角设定（必须有明显缺陷）
"""


def build_plot_prompt(style_json: Dict, user_setting: Dict, world: str = "", reference_text: str = "") -> str:
    return f"""【生成目标】PLOT
你是小说剧情结构设计师。

必须严格模仿以下写作风格，并让剧情结构能服务后续正文写作。

【风格规则】
{_json(style_json)}

【参考文本摘要】
{summarize_reference(reference_text)}

【世界观】
{world}

【用户设定】
灵感：{user_setting.get("inspiration", "")}
题材：{user_setting.get("genre", "")}
地点：{user_setting.get("location", "")}
背景：{user_setting.get("background", "")}
人物设定：{user_setting.get("characters", "")}
文风模块：{user_setting.get("writing_style", "")}
模板模块：{user_setting.get("template", "")}
公有库逻辑：{user_setting.get("public_library", "")}

请生成：
1. 故事主线
2. 三幕式或章节式剧情大纲
3. 第一章关键事件
4. 主要人物关系变化
5. 结尾悬念
"""


def build_novel_prompt(style_json: Dict, world: str, plot: str, user_setting: Dict, reference_text: str = "") -> str:
    return f"""【生成目标】NOVEL
你是小说写作者。

必须严格遵循：

- 风格规则
- 世界观设定
- 用户设定

【风格规则】
{_json(style_json)}

【参考文本摘要】
{summarize_reference(reference_text)}

【用户设定】
灵感：{user_setting.get("inspiration", "")}
题材：{user_setting.get("genre", "")}
地点：{user_setting.get("location", "")}
背景：{user_setting.get("background", "")}
人物设定：{user_setting.get("characters", "")}
文风模块：{user_setting.get("writing_style", "")}
模板模块：{user_setting.get("template", "")}
公有库逻辑：{user_setting.get("public_library", "")}

【世界观】
{world}

【剧情结构】
{plot}

请生成第一章小说正文：

要求：
- 必须贴合参考文本语言风格
- 禁止脱离设定自由发挥
- 避免AI式总结和说明
- 使用人物行为推动剧情
- 保持一致叙事节奏与语言习惯
"""


def _json(data: Dict) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)
