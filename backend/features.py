import html
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from .analyzer import analyze_text


PUBLIC_LIBRARIES: Dict[str, Dict[str, str]] = {
    "爽文升级": {
        "logic": "弱势开局、明确压迫、快速打脸、阶段性奖励、持续升级。",
        "style": "句子直接，冲突前置，每一场戏都要给主角一个可见收益。",
    },
    "悬疑反转": {
        "logic": "异常细节、错误答案、局部真相、证词矛盾、结尾反证。",
        "style": "克制叙述，线索藏在动作和环境里，避免提前解释谜底。",
    },
    "情绪虐恋": {
        "logic": "误会、亏欠、迟来的真相、关系拉扯、情绪偿还。",
        "style": "强调细节回声，用沉默、停顿和反复出现的小物件承载情绪。",
    },
    "群像权谋": {
        "logic": "多方目标错位、利益交换、明暗盟约、阶段性牺牲。",
        "style": "信息密度高，台词含有潜台词，人物动机不能单薄。",
    },
}


def generate_cover_svg(title: str, subtitle: str, setting: Dict[str, str]) -> str:
    safe_title = html.escape(title or _title_from_setting(setting))
    title_lines = _svg_title_lines(title or _title_from_setting(setting))
    safe_subtitle = html.escape(subtitle or setting.get("genre") or "原创长篇小说")
    genre = setting.get("genre", "")
    palette = _cover_palette(genre)
    motif = _cover_motif(genre)
    title_svg = "\n".join(
        f'    <tspan x="360" dy="{0 if index == 0 else 72}">{html.escape(line)}</tspan>'
        for index, line in enumerate(title_lines)
    )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="720" height="1040" viewBox="0 0 720 1040" role="img" aria-label="{safe_title}">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="{palette[0]}"/>
      <stop offset="0.58" stop-color="{palette[1]}"/>
      <stop offset="1" stop-color="{palette[2]}"/>
    </linearGradient>
    <filter id="grain">
      <feTurbulence baseFrequency="0.72" numOctaves="2" seed="7"/>
      <feColorMatrix type="saturate" values="0"/>
      <feComponentTransfer><feFuncA type="table" tableValues="0 0.16"/></feComponentTransfer>
    </filter>
  </defs>
  <rect width="720" height="1040" fill="url(#bg)"/>
  <rect width="720" height="1040" filter="url(#grain)" opacity="0.22"/>
  <rect x="54" y="64" width="612" height="912" rx="10" fill="none" stroke="rgba(255,255,255,0.62)" stroke-width="2"/>
  <path d="{motif}" fill="none" stroke="rgba(255,255,255,0.52)" stroke-width="5" stroke-linecap="round"/>
  <text x="360" y="400" text-anchor="middle" fill="#fff" font-size="54" font-weight="700" font-family="serif">
{title_svg}
  </text>
  <line x1="198" y1="556" x2="522" y2="556" stroke="rgba(255,255,255,0.72)" stroke-width="2"/>
  <text x="360" y="616" text-anchor="middle" fill="rgba(255,255,255,0.9)" font-size="24" letter-spacing="3" font-family="sans-serif">{safe_subtitle}</text>
  <text x="360" y="896" text-anchor="middle" fill="rgba(255,255,255,0.78)" font-size="20" font-family="sans-serif">AI NOVEL STUDIO</text>
</svg>"""


def deconstruct_book(text: str) -> Dict[str, object]:
    style = analyze_text(text).model_dump()
    chapters = _split_chapters(text)
    hooks = _find_sentences(text, ("突然", "可是", "但", "然而", "秘密", "死", "消失", "真相"))
    conflicts = _find_sentences(text, ("争", "恨", "怕", "骗", "杀", "逃", "欠", "威胁", "背叛"))
    return {
        "style": style,
        "structure": [
            f"样本拆分为 {len(chapters)} 个章节/段落单元。",
            "开篇优先建立异常、目标或情绪债。",
            "中段通过阻碍、误会或线索反转延长张力。",
            "结尾保留一个未兑现问题，推动下一章点击。",
        ],
        "hooks": hooks[:8],
        "conflicts": conflicts[:8],
        "imitation_rules": [
            "保留原文叙事视角、句式长度和情绪释放方式。",
            "替换人物、地点和核心事件，避免复刻具体桥段。",
            "学习冲突递进顺序，而不是照搬设定名词。",
            "每章结尾设置一个信息差、关系差或危险差。",
        ],
    }


def review_text(text: str) -> Dict[str, List[str]]:
    length = len(text.strip())
    dialogue_count = text.count("“") + text.count('"')
    paragraphs = [p for p in text.splitlines() if p.strip()]
    highlights = []
    suggestions = []
    ai_detection = []

    if length > 1200:
        highlights.append("篇幅足够承载完整场景，具备章节雏形。")
    if dialogue_count >= 4:
        highlights.append("对话占比明显，有利于推动冲突和人物关系。")
    if any(word in text for word in ("血", "雨", "灯", "门", "风", "影")):
        highlights.append("场景物象较清晰，具备可延展的氛围锚点。")
    if not highlights:
        highlights.append("文本已有基本叙事方向，可以继续强化冲突和细节。")

    if length < 800:
        suggestions.append("正文偏短，建议补足一个完整事件：触发、阻碍、选择、后果。")
    if len(paragraphs) < 5:
        suggestions.append("段落层次较少，可按动作、心理、对话、反应拆开。")
    if "忽然" in text and text.count("忽然") > 3:
        suggestions.append("突发转折词重复较多，可改成动作或环境变化。")
    suggestions.append("每章末尾补一个未解决问题，让读者有继续阅读的理由。")

    generic_words = sum(text.count(word) for word in ("命运", "内心深处", "无法言说", "仿佛", "意义"))
    if generic_words >= 5:
        ai_detection.append("存在抽象抒情词集中出现的风险，建议改为具体动作和感官细节。")
    if "总之" in text or "综上" in text:
        ai_detection.append("出现总结式表达，小说正文中建议删除。")
    if not ai_detection:
        ai_detection.append("未发现明显模板化总结口吻，但仍建议人工复核关键情节原创性。")

    return {"ai_detection": ai_detection, "highlights": highlights, "suggestions": suggestions}


def chapter_intelligence(text: str) -> Dict[str, List[str]]:
    sentences = _sentences(text)
    return {
        "main_line": _pick(sentences, ("找到", "发现", "决定", "真相", "目标", "任务")),
        "side_line": _pick(sentences, ("朋友", "邻居", "旧事", "传闻", "支线", "旁人")),
        "romance_line": _pick(sentences, ("喜欢", "拥抱", "沉默", "眼神", "心", "吻", "爱")),
        "faction_line": _pick(sentences, ("势力", "家族", "公司", "门派", "管理局", "联盟", "敌人")),
        "risks": _chapter_risks(text),
    }


def query_info(query: str, platform: str = "") -> Dict[str, List[str]]:
    q = query.strip() or "小说创作"
    platform_text = f"，重点参考{platform}" if platform else ""
    return {
        "answer": [
            f"可围绕“{q}”{platform_text}拆成题材热度、读者期待、更新节奏、签约规则和同类作品结构五类信息。",
            "本地版不直接抓取实时网页；接入搜索 API 后，这个接口可以替换为实时平台资讯查询。",
        ],
        "keywords": [f"{q} 榜单", f"{q} 签约", f"{q} 爆款结构", f"{q} 读者偏好", f"{q} 更新节奏"],
        "actions": [
            "先查同题材榜单前三十本，记录书名、简介、开篇冲突和章节节奏。",
            "对比平台福利与签约门槛，决定日更字数和章节长度。",
            "把高频卖点转成自己的设定，不直接复制人设和桥段。",
        ],
    }


def generate_directions(setting: Dict[str, str]) -> List[str]:
    protagonist = setting.get("characters") or "主角"
    genre = setting.get("genre") or "故事"
    return [
        f"路线 A：{protagonist}选择正面突破，{genre}冲突升级，短期爽感强。",
        "路线 B：主角暂时妥协，转入暗线调查，悬念和反转空间更大。",
        "路线 C：配角背叛或牺牲，感情线与主线绑定，情绪冲击更强。",
        "路线 D：敌对势力给出合作条件，进入权谋或多方博弈结构。",
    ]


def append_history(path: Path, kind: str, title: str, content: str) -> Dict[str, str]:
    path.parent.mkdir(parents=True, exist_ok=True)
    records = read_history(path)
    record = {
        "kind": kind,
        "title": title or kind,
        "content": content,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    records.insert(0, record)
    path.write_text(json.dumps(records[:100], ensure_ascii=False, indent=2), encoding="utf-8")
    return record


def read_history(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []


def _title_from_setting(setting: Dict[str, str]) -> str:
    inspiration = setting.get("inspiration") or setting.get("background") or setting.get("genre")
    if not inspiration:
        return "未命名之书"
    title = re.split(r"[，。！？\n,.!?]", inspiration.strip())[0]
    return title[:12] or "未命名之书"


def _svg_title_lines(title: str) -> List[str]:
    clean = (title or "未命名之书").strip()
    if len(clean) <= 8:
        return [clean]
    if len(clean) <= 16:
        return [clean[:8], clean[8:]]
    return [clean[:8], clean[8:16], clean[16:24]]


def _cover_palette(genre: str) -> List[str]:
    if any(word in genre for word in ("悬疑", "惊悚", "刑侦")):
        return ["#111827", "#29524a", "#9a6a19"]
    if any(word in genre for word in ("科幻", "未来", "机甲")):
        return ["#102033", "#0f766e", "#b7d8ff"]
    if any(word in genre for word in ("玄幻", "仙侠", "修真")):
        return ["#1f2337", "#6b4e9b", "#d8b15f"]
    if any(word in genre for word in ("都市", "情感", "言情")):
        return ["#263238", "#9a6a6a", "#f1c27d"]
    return ["#23211d", "#0f766e", "#9a6a19"]


def _cover_motif(genre: str) -> str:
    if any(word in genre for word in ("悬疑", "惊悚", "刑侦")):
        return "M148 284 C248 188 472 188 572 284 M360 250 L360 780 M232 724 C290 792 430 792 488 724"
    if any(word in genre for word in ("科幻", "未来", "机甲")):
        return "M162 312 L360 184 L558 312 L514 722 L360 838 L206 722 Z M230 344 L490 344"
    if any(word in genre for word in ("玄幻", "仙侠", "修真")):
        return "M360 170 C422 318 550 378 524 536 C500 684 392 744 360 870 C328 744 220 684 196 536 C170 378 298 318 360 170"
    return "M160 320 C280 250 440 250 560 320 M210 730 C300 660 420 660 510 730 M360 280 L360 820"


def _split_chapters(text: str) -> List[str]:
    parts = re.split(r"(?:第[一二三四五六七八九十百千万\d]+章|Chapter\s+\d+)", text)
    return [part.strip() for part in parts if part.strip()] or [text]


def _sentences(text: str) -> List[str]:
    return [s.strip() for s in re.split(r"(?<=[。！？!?])", text) if s.strip()]


def _find_sentences(text: str, keywords) -> List[str]:
    return [s for s in _sentences(text) if any(word in s for word in keywords)]


def _pick(sentences: List[str], keywords) -> List[str]:
    picked = [s for s in sentences if any(word in s for word in keywords)]
    return (picked or sentences[:2] or ["暂无明确线索"])[:5]


def _chapter_risks(text: str) -> List[str]:
    risks = []
    if len(text) < 1000:
        risks.append("章节信息量偏少，主线推进可能不够。")
    if text.count("“") < 2:
        risks.append("对话偏少，人物关系变化可能不够直观。")
    if not any(word in text for word in ("但是", "可是", "然而", "突然", "没想到")):
        risks.append("转折信号较弱，建议补一个阻碍或反转。")
    return risks or ["章节结构基本稳定，重点检查伏笔回收。"]
