import re
from collections import Counter
from typing import Dict, List

from .models import StyleAnalysis


FIRST_PERSON_MARKERS = ("我", "我们", "俺")
THIRD_PERSON_MARKERS = ("他", "她", "他们", "她们", "它")
ACTION_MARKERS = ("走", "跑", "推", "抓", "看", "听", "站", "坐", "打开", "关上", "冲", "停")
PSYCHOLOGICAL_MARKERS = ("想", "觉得", "意识到", "明白", "记得", "害怕", "担心", "后悔", "怀疑")
DIALOGUE_MARKERS = ("“", "”", "\"", "：", ":")


def analyze_text(text: str) -> StyleAnalysis:
    clean_text = _normalize_text(text)
    if not clean_text:
        return StyleAnalysis(
            style="样本不足，无法判断明确文风",
            perspective="未知",
            pace="未知",
            emotion="中性",
            narrative_mode="未知",
            writing_rules=["先上传或粘贴足够长的参考文本，再进行风格分析。"],
        )

    sentences = _split_sentences(clean_text)
    avg_sentence_length = _average_sentence_length(sentences)
    dialogue_ratio = _count_markers(clean_text, DIALOGUE_MARKERS) / max(len(sentences), 1)
    paragraph_lengths = [len(p.strip()) for p in clean_text.splitlines() if p.strip()]

    perspective = _detect_perspective(clean_text)
    pace = _detect_pace(avg_sentence_length, dialogue_ratio, paragraph_lengths)
    emotion = _detect_emotion(clean_text)
    narrative_mode = _detect_narrative_mode(clean_text)
    style = _detect_style(clean_text, avg_sentence_length, dialogue_ratio, emotion)
    rules = _build_rules(style, perspective, pace, emotion, narrative_mode, avg_sentence_length, dialogue_ratio)

    return StyleAnalysis(
        style=style,
        perspective=perspective,
        pace=pace,
        emotion=emotion,
        narrative_mode=narrative_mode,
        writing_rules=rules,
    )


def summarize_reference(text: str, max_chars: int = 900) -> str:
    clean_text = _normalize_text(text)
    if len(clean_text) <= max_chars:
        return clean_text

    paragraphs = [p.strip() for p in clean_text.splitlines() if p.strip()]
    summary_parts: List[str] = []
    total = 0
    for paragraph in paragraphs:
        if total + len(paragraph) > max_chars:
            break
        summary_parts.append(paragraph)
        total += len(paragraph)

    if summary_parts:
        return "\n".join(summary_parts)
    return clean_text[:max_chars]


def _normalize_text(text: str) -> str:
    return re.sub(r"\n{3,}", "\n\n", text or "").strip()


def _split_sentences(text: str) -> List[str]:
    parts = re.split(r"(?<=[。！？!?；;])", text)
    return [p.strip() for p in parts if p.strip()]


def _average_sentence_length(sentences: List[str]) -> float:
    if not sentences:
        return 0.0
    return sum(len(sentence) for sentence in sentences) / len(sentences)


def _count_markers(text: str, markers) -> int:
    return sum(text.count(marker) for marker in markers)


def _detect_perspective(text: str) -> str:
    first = _count_markers(text, FIRST_PERSON_MARKERS)
    third = _count_markers(text, THIRD_PERSON_MARKERS)
    if first == 0 and third == 0:
        return "第三人称或客观叙述"
    if first >= third * 0.75:
        return "第一人称"
    return "第三人称"


def _detect_pace(avg_sentence_length: float, dialogue_ratio: float, paragraph_lengths: List[int]) -> str:
    avg_paragraph = sum(paragraph_lengths) / len(paragraph_lengths) if paragraph_lengths else 0
    if avg_sentence_length <= 24 or dialogue_ratio >= 0.55 or avg_paragraph <= 90:
        return "快节奏"
    if avg_sentence_length >= 45 and avg_paragraph >= 180:
        return "慢节奏"
    return "中等节奏"


def _detect_emotion(text: str) -> str:
    lexicons: Dict[str, List[str]] = {
        "压抑": ["冷", "黑", "沉", "痛", "死", "血", "空", "暗", "疲惫", "窒息", "绝望"],
        "紧张": ["突然", "立刻", "马上", "危险", "尖叫", "追", "逃", "枪", "刀", "爆炸"],
        "温柔": ["轻", "暖", "笑", "柔", "春", "灯", "安静", "温热", "拥抱"],
        "荒诞": ["怪", "滑稽", "莫名", "离谱", "可笑", "奇怪", "疯"],
        "冷峻": ["没有", "只是", "沉默", "灰", "硬", "干净", "命令", "规矩"],
    }
    scores = {name: sum(text.count(word) for word in words) for name, words in lexicons.items()}
    best, score = max(scores.items(), key=lambda item: item[1])
    return best if score > 0 else "中性克制"


def _detect_narrative_mode(text: str) -> str:
    scores = {
        "动作驱动": _count_markers(text, ACTION_MARKERS),
        "心理驱动": _count_markers(text, PSYCHOLOGICAL_MARKERS),
        "对话驱动": _count_markers(text, DIALOGUE_MARKERS) * 2,
    }
    best, _ = max(scores.items(), key=lambda item: item[1])
    return best


def _detect_style(text: str, avg_sentence_length: float, dialogue_ratio: float, emotion: str) -> str:
    punctuation = Counter(ch for ch in text if ch in "，。！？；：、“”")
    exclamation_density = punctuation.get("！", 0) / max(len(text), 1)

    descriptors = []
    if avg_sentence_length <= 24:
        descriptors.append("短句密集")
    elif avg_sentence_length >= 45:
        descriptors.append("长句铺陈")
    else:
        descriptors.append("句式平衡")

    if dialogue_ratio >= 0.55:
        descriptors.append("对话感强")
    if exclamation_density > 0.01:
        descriptors.append("情绪外放")
    else:
        descriptors.append("表达克制")

    if emotion in {"压抑", "冷峻"}:
        descriptors.append("冷峻压抑")
    elif emotion == "温柔":
        descriptors.append("细腻温柔")
    elif emotion == "紧张":
        descriptors.append("紧张凌厉")
    elif emotion == "荒诞":
        descriptors.append("轻微荒诞")
    else:
        descriptors.append("中性写实")

    return "、".join(descriptors)


def _build_rules(
    style: str,
    perspective: str,
    pace: str,
    emotion: str,
    narrative_mode: str,
    avg_sentence_length: float,
    dialogue_ratio: float,
) -> List[str]:
    rules = [
        f"叙事视角保持为{perspective}，不要频繁切换观察位置。",
        f"整体节奏保持{pace}，段落推进速度与参考文本一致。",
        f"情绪基调保持{emotion}，避免突然转向热血、鸡汤或说明文口吻。",
        f"叙事方式以{narrative_mode}为主，让事件通过人物行为、感受或对话自然展开。",
        "避免直接总结主题，不用泛泛的AI式解释替代场景。",
        "保留参考文本的句式密度、停顿习惯和描写颗粒度。",
    ]

    if avg_sentence_length <= 24:
        rules.append("多用短句和明确动作，减少过长的背景说明。")
    elif avg_sentence_length >= 45:
        rules.append("允许较长句铺陈心理、环境和因果，但句意必须清楚。")

    if dialogue_ratio >= 0.55:
        rules.append("用对话推动冲突，旁白只补足必要动作和气氛。")
    else:
        rules.append("对话克制使用，主要依靠叙述、动作和环境细节推进。")

    if "冷峻" in style or emotion == "压抑":
        rules.append("语言保持克制，不夸张渲染，不用华丽比喻堆砌情绪。")
    if "细腻" in style or emotion == "温柔":
        rules.append("保留细小感官描写，让情绪从触感、光线和动作中显露。")

    return rules
