import os
import re
from typing import Dict, List


def call_llm(prompt: str) -> str:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if api_key:
        try:
            return _call_openai(prompt, api_key)
        except Exception as exc:
            return _fallback_generate(prompt, warning=f"OpenAI 调用失败，已切换本地演示生成：{exc}")
    return _fallback_generate(prompt)


def _call_openai(prompt: str, api_key: str) -> str:
    from openai import OpenAI

    client = OpenAI(api_key=api_key)
    model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
    response = client.responses.create(
        model=model,
        input=[
            {
                "role": "system",
                "content": "你是严谨的中文小说生成助手。必须优先模仿参考文本的文风、节奏和叙事方式。",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=float(os.getenv("OPENAI_TEMPERATURE", "0.85")),
    )
    return response.output_text


def _fallback_generate(prompt: str, warning: str = "") -> str:
    target = _extract_target(prompt)
    style = _extract_json_like(prompt, "风格规则")
    setting = _extract_setting(prompt)
    tone = _style_tone(style)

    if target == "WORLD":
        content = _generate_world(setting, tone)
    elif target == "PLOT":
        content = _generate_plot(setting, tone, _section(prompt, "世界观"))
    elif target == "NOVEL":
        content = _generate_novel(setting, tone, _section(prompt, "世界观"), _section(prompt, "剧情结构"))
    else:
        content = "无法识别生成目标。"

    if warning:
        return f"{warning}\n\n{content}"
    return content


def _extract_target(prompt: str) -> str:
    match = re.search(r"【生成目标】([A-Z_]+)", prompt)
    return match.group(1) if match else ""


def _extract_json_like(prompt: str, title: str) -> str:
    return _section(prompt, title)


def _section(prompt: str, title: str) -> str:
    pattern = rf"【{re.escape(title)}】\n(.*?)(?=\n【|\Z)"
    match = re.search(pattern, prompt, flags=re.S)
    return match.group(1).strip() if match else ""


def _extract_setting(prompt: str) -> Dict[str, str]:
    block = _section(prompt, "用户设定")
    result: Dict[str, str] = {}
    mapping = {
        "inspiration": "灵感",
        "genre": "题材",
        "location": "地点",
        "background": "背景",
        "characters": "人物设定",
        "writing_style": "文风模块",
        "template": "模板模块",
        "public_library": "公有库逻辑",
    }
    for key, label in mapping.items():
        match = re.search(
            rf"{label}：(.*?)(?=\n(?:灵感|题材|地点|背景|人物设定|文风模块|模板模块|公有库逻辑)：|\Z)",
            block,
            flags=re.S,
        )
        result[key] = match.group(1).strip() if match else ""
    return result


def _style_tone(style_text: str) -> Dict[str, str]:
    text = style_text or ""
    short = "短句" in text or "快节奏" in text
    first_person = "第一人称" in text
    cold = any(word in text for word in ("冷峻", "压抑", "克制"))
    dialogue = "对话驱动" in text or "对话感强" in text
    return {
        "sentence": "short" if short else "balanced",
        "perspective": "first" if first_person else "third",
        "emotion": "cold" if cold else "observant",
        "mode": "dialogue" if dialogue else "narrative",
    }


def _generate_world(setting: Dict[str, str], tone: Dict[str, str]) -> str:
    genre = setting.get("genre") or "悬疑"
    location = setting.get("location") or "一座边境城市"
    background = setting.get("background") or "旧制度还在运转，新秩序迟迟没有抵达"
    characters = setting.get("characters") or "一个不擅长表达的人，被迫卷入失踪案"
    inspiration = setting.get("inspiration") or "一个不该被打开的秘密"
    public_library = setting.get("public_library") or "线索递进、冲突升级、人物付出代价"

    lines = [
        "1. 世界观设定",
        _line(f"{location}被一套看不见的规矩拴住。{background}。灵感核心是：{inspiration}。街道、档案、身份和记忆都可以被登记，也都可以被抹掉。", tone),
        "",
        "2. 核心冲突",
        _line(f"{genre}的外壳之下，真正的冲突不是谁赢，而是谁还能保留自己说真话的资格。主角从{characters}开始，被迫查清一件人人都假装结束的事。", tone),
        "",
        "3. 势力结构",
        _line(f"城内有三股力量：掌握登记权的管理局，靠沉默换取安全的地方家族，以及在废弃区域交换消息的无名者。底层逻辑采用{public_library}。三方都需要主角，也都准备牺牲主角。", tone),
        "",
        "4. 主角设定（必须有明显缺陷）",
        _line("主角敏锐，却不信任任何亲近关系；能看见细节，却常把人的善意也当成陷阱。这个缺陷会让线索变得清楚，也会让他一次次错过获救的机会。", tone),
    ]
    return "\n".join(lines)


def _generate_plot(setting: Dict[str, str], tone: Dict[str, str], world: str) -> str:
    location = setting.get("location") or "城里"
    characters = setting.get("characters") or "主角"
    return "\n".join(
        [
            "1. 故事主线",
            _line(f"{characters}在{location}发现一份不该存在的记录。记录指向旧案，也指向主角自己被删改过的过去。", tone),
            "",
            "2. 剧情大纲",
            _line("第一幕：主角接触异常，拒绝卷入，却被现实逼到案发现场。", tone),
            _line("第二幕：线索逐渐相互抵触，可靠的人开始撒谎，敌对的人反而留下帮助。", tone),
            _line("第三幕：主角找到真相的入口，却发现真相需要他承认自己一直逃避的过错。", tone),
            "",
            "3. 第一章关键事件",
            _line("雨夜或清晨，主角收到一个被注销者留下的物件。物件很轻，后果很重。第一个追踪者出现，主角第一次说谎。", tone),
            "",
            "4. 主要人物关系变化",
            _line("主角与同伴从互相利用变成短暂信任，但这种信任建立在未说出口的秘密上。", tone),
            "",
            "5. 结尾悬念",
            _line("第一章末尾，主角在档案背面看见自己的签名。日期却是三年前。", tone),
        ]
    )


def _generate_novel(setting: Dict[str, str], tone: Dict[str, str], world: str, plot: str) -> str:
    location = setting.get("location") or "城里"
    character = _first_character(setting.get("characters") or "许临，一个沉默的档案员")
    narrator = "我" if tone["perspective"] == "first" else character
    paragraphs = _novel_paragraphs(narrator, location, setting, tone)
    title = "第一章 旧记录"
    return title + "\n\n" + "\n\n".join(paragraphs)


def _novel_paragraphs(narrator: str, location: str, setting: Dict[str, str], tone: Dict[str, str]) -> List[str]:
    first = tone["perspective"] == "first"
    subject = "我" if first else narrator
    possessive = "我的" if first else "他的"
    genre = setting.get("genre") or "悬疑"
    background = setting.get("background") or "旧制度仍在"

    if tone["sentence"] == "short":
        paragraphs = [
            f"{location}的雨下到第五天。水从屋檐落下来，砸在铁皮桶里，一声一声，像有人在暗处敲门。",
            f"{subject}把灯拧亮。桌上放着一只灰色信封。没有邮戳。没有署名。封口处沾着一点干硬的泥。",
            f"{possessive}手停了一下。{genre}故事里，麻烦总是这样开始。它不喊人，只是安静地等着你伸手。",
            f"信封里只有一张登记表。纸很薄，边角被水泡软。姓名一栏被划掉，编号还在。最下面有一行小字：此人从未存在。",
            f"{subject}看了很久。窗外有脚步声停在楼下。一步，两步。然后是很轻的咳嗽。",
            "电话在这时响起来。",
            f"{subject}没有接。铃声响了七下，自己断了。紧接着，门缝下面塞进来第二张纸。",
            f"纸上是{possessive}签名。日期是三年前。",
        ]
    else:
        paragraphs = [
            f"{location}的雨已经下了五天，街面被洗成一种旧铁似的颜色，连路灯也显得疲惫，光落在积水里，碎得没有一点声响。",
            f"{subject}回到房间时，桌上多了一只灰色信封。它摆在台灯下面，像早就属于那里，封口处沾着干硬的泥，除此之外没有邮戳，也没有任何能够说明来处的字。",
            f"{background}。在这样的地方，东西不会无缘无故出现。人也不会。{subject}明白这一点，所以没有立刻伸手。",
            f"信封里是一张登记表，纸页被潮气泡软，姓名栏被粗暴地划去，只剩下一串编号。编号下面，有人用很淡的墨水写着：此人从未存在。",
            f"这句话让房间安静下来。不是没有声音，而是所有声音都退到了墙后。水管在响，窗外有人经过，远处的车轮压过积水，{subject}却只听见自己的呼吸。",
            f"楼下传来脚步声。那人停在门洞里，没有上楼，也没有离开。过了一会儿，电话响了。",
            f"{subject}等铃声自己断掉。门缝下很快塞进来第二张纸。纸面朝上，干净得不正常。",
            f"上面是{possessive}签名。日期写着三年前。那一年，{subject}还没有来过这里。",
        ]

    if tone["mode"] == "dialogue":
        paragraphs.insert(
            -1,
            f"“别开门。”电话那头终于有人说。\n\n{subject}问：“你是谁？”\n\n对方沉默了一秒。“一个已经不存在的人。”",
        )
    return paragraphs


def _line(text: str, tone: Dict[str, str]) -> str:
    if tone["sentence"] == "short":
        sentences = re.split(r"(?<=[。！？])", text)
        return "".join(sentence.strip() for sentence in sentences if sentence.strip())
    return text


def _first_character(characters: str) -> str:
    text = characters.strip()
    if not text:
        return "许临"
    for separator in ("，", ",", "。", "\n", " "):
        if separator in text:
            return text.split(separator)[0].strip() or "许临"
    return text[:8]
