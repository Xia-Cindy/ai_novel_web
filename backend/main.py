from datetime import date
from pathlib import Path
from typing import Any, Dict

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .analyzer import analyze_text
from .features import (
    PUBLIC_LIBRARIES,
    append_history,
    chapter_intelligence,
    deconstruct_book,
    generate_cover_svg,
    generate_directions as build_directions,
    query_info as query_local_info,
    read_history,
    review_text,
)
from .llm import call_llm
from .models import (
    CacheState,
    CheckinResponse,
    ChapterIntelResponse,
    CoverRequest,
    CoverResponse,
    DirectionRequest,
    DraftPackageResponse,
    GenerateNovelRequest,
    GeneratePlotRequest,
    GenerationResponse,
    HistoryRecord,
    InfoQuery,
    TextPayload,
    UserSetting,
)
from .prompt_engine import build_novel_prompt, build_plot_prompt, build_world_prompt


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
FRONTEND_DIR = BASE_DIR / "frontend"
REFERENCE_FILE = DATA_DIR / "reference.txt"
HISTORY_FILE = DATA_DIR / "history.json"
CHECKIN_FILE = DATA_DIR / "checkin.json"

app = FastAPI(title="AI 小说风格仿写生成系统")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

reference_cache: Dict[str, Any] = {}


@app.on_event("startup")
def load_cached_reference() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if REFERENCE_FILE.exists():
        text = REFERENCE_FILE.read_text(encoding="utf-8")
        if text.strip():
            reference_cache["text"] = text


@app.get("/")
def index() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/public_libraries")
def public_libraries() -> Dict[str, Dict[str, str]]:
    return PUBLIC_LIBRARIES


@app.get("/cache_state", response_model=CacheState)
def cache_state() -> CacheState:
    text = reference_cache.get("text", "")
    style = reference_cache.get("style")
    return CacheState(
        has_reference=bool(text),
        has_style=bool(style),
        reference_length=len(text),
        style=style,
    )


@app.post("/upload_reference")
async def upload_reference(request: Request) -> Dict[str, Any]:
    text = ""
    source = "text"
    content_type = request.headers.get("content-type", "")

    if "multipart/form-data" in content_type:
        form = await request.form()
        file = form.get("file")
        pasted_text = str(form.get("text") or "")
        if file is not None and hasattr(file, "read"):
            raw = await file.read()
            text = raw.decode("utf-8")
            source = getattr(file, "filename", None) or "upload"
        else:
            text = pasted_text
    else:
        payload = await request.json()
        text = str(payload.get("text", ""))

    if not text.strip():
        raise HTTPException(status_code=400, detail="参考文本不能为空")

    reference_cache["text"] = text
    reference_cache.pop("style", None)
    REFERENCE_FILE.write_text(text, encoding="utf-8")
    return {"status": "ok", "source": source, "length": len(text)}


@app.post("/upload_reference_file")
async def upload_reference_file(request: Request) -> Dict[str, Any]:
    form = await request.form()
    file = form.get("file")
    if file is None or not hasattr(file, "read"):
        raise HTTPException(status_code=400, detail="请选择 TXT 文件")

    raw = await file.read()
    text = raw.decode("utf-8")
    if not text.strip():
        raise HTTPException(status_code=400, detail="参考文本不能为空")

    reference_cache["text"] = text
    reference_cache.pop("style", None)
    REFERENCE_FILE.write_text(text, encoding="utf-8")
    return {"status": "ok", "source": getattr(file, "filename", None) or "upload", "length": len(text)}


@app.post("/analyze_reference")
def analyze_reference() -> Dict[str, Any]:
    text = _reference_text()
    result = _dump_model(analyze_text(text))
    reference_cache["style"] = result
    return result


@app.post("/generate_world", response_model=GenerationResponse)
def generate_world(req: UserSetting) -> GenerationResponse:
    style = _style_result()
    text = _reference_text()
    prompt = build_world_prompt(style, _dump_model(req), text)
    content = call_llm(prompt)
    reference_cache["world"] = content
    append_history(HISTORY_FILE, "world", "世界观", content)
    return GenerationResponse(content=content, prompt=prompt)


@app.post("/generate_plot", response_model=GenerationResponse)
def generate_plot(req: GeneratePlotRequest) -> GenerationResponse:
    style = _style_result()
    text = _reference_text()
    world = req.world or reference_cache.get("world", "")
    prompt = build_plot_prompt(style, _dump_model(req), world, text)
    content = call_llm(prompt)
    reference_cache["plot"] = content
    append_history(HISTORY_FILE, "outline", "剧情大纲", content)
    return GenerationResponse(content=content, prompt=prompt)


@app.post("/generate_outline", response_model=GenerationResponse)
def generate_outline(req: GeneratePlotRequest) -> GenerationResponse:
    return generate_plot(req)


@app.post("/generate_novel", response_model=GenerationResponse)
def generate_novel(req: GenerateNovelRequest) -> GenerationResponse:
    style = _style_result()
    text = _reference_text()
    prompt = build_novel_prompt(style, req.world, req.plot, _dump_model(req), text)
    content = call_llm(prompt)
    reference_cache["novel"] = content
    append_history(HISTORY_FILE, "novel", "第一章正文", content)
    return GenerationResponse(content=content, prompt=prompt)


@app.post("/generate_cover", response_model=CoverResponse)
def generate_cover(req: CoverRequest) -> CoverResponse:
    setting = _dump_model(req)
    title = req.title or _infer_title(setting)
    svg = generate_cover_svg(title, req.subtitle, setting)
    append_history(HISTORY_FILE, "cover", title, svg)
    return CoverResponse(title=title, svg=svg)


@app.post("/generate_directions")
def generate_directions(req: DirectionRequest) -> Dict[str, Any]:
    directions = build_directions(_dump_model(req))
    append_history(HISTORY_FILE, "directions", "剧情走向", "\n".join(directions))
    return {"directions": directions}


@app.post("/generate_all", response_model=DraftPackageResponse)
def generate_all(req: CoverRequest) -> DraftPackageResponse:
    style = _style_result()
    text = _reference_text()
    setting = _dump_model(req)

    world_prompt = build_world_prompt(style, setting, text)
    world = call_llm(world_prompt)
    reference_cache["world"] = world

    plot_prompt = build_plot_prompt(style, setting, world, text)
    outline = call_llm(plot_prompt)
    reference_cache["plot"] = outline

    novel_req = {**setting, "world": world, "plot": outline}
    novel_prompt = build_novel_prompt(style, world, outline, novel_req, text)
    novel = call_llm(novel_prompt)
    reference_cache["novel"] = novel

    title = req.title or _infer_title(setting)
    cover = CoverResponse(title=title, svg=generate_cover_svg(title, req.subtitle, setting))
    directions = build_directions(setting)

    append_history(HISTORY_FILE, "outline", "一键生成大纲", outline)
    append_history(HISTORY_FILE, "cover", title, cover.svg)
    append_history(HISTORY_FILE, "novel", "一键生成正文", novel)
    append_history(HISTORY_FILE, "directions", "一键生成剧情走向", "\n".join(directions))

    return DraftPackageResponse(outline=outline, cover=cover, novel=novel, directions=directions)


@app.post("/deconstruct_book")
def deconstruct(payload: TextPayload) -> Dict[str, Any]:
    if not payload.text.strip():
        raise HTTPException(status_code=400, detail="拆书文本不能为空")
    result = deconstruct_book(payload.text)
    append_history(HISTORY_FILE, "deconstruct", payload.title or "拆书报告", str(result))
    return result


@app.post("/review_text")
def review(payload: TextPayload) -> Dict[str, Any]:
    if not payload.text.strip():
        raise HTTPException(status_code=400, detail="审稿文本不能为空")
    result = review_text(payload.text)
    append_history(HISTORY_FILE, "review", payload.title or "审稿报告", str(result))
    return result


@app.post("/summarize_chapter", response_model=ChapterIntelResponse)
def summarize_chapter(payload: TextPayload) -> ChapterIntelResponse:
    if not payload.text.strip():
        raise HTTPException(status_code=400, detail="章节正文不能为空")
    result = chapter_intelligence(payload.text)
    append_history(HISTORY_FILE, "chapter_intel", payload.title or "章节情报", str(result))
    return ChapterIntelResponse(**result)


@app.post("/query_info")
def query_info(payload: InfoQuery) -> Dict[str, Any]:
    result = query_local_info(payload.query, payload.platform)
    append_history(HISTORY_FILE, "info", payload.query or "平台资讯", str(result))
    return result


@app.get("/history", response_model=list[HistoryRecord])
def history() -> list[HistoryRecord]:
    return [HistoryRecord(**record) for record in read_history(HISTORY_FILE)]


@app.post("/daily_checkin", response_model=CheckinResponse)
def daily_checkin() -> CheckinResponse:
    today = date.today().isoformat()
    if CHECKIN_FILE.exists():
        data = _read_json(CHECKIN_FILE)
        if data.get("date") == today:
            return CheckinResponse(claimed=False, words=0, message="今天已经领取过 2500 字。")

    CHECKIN_FILE.write_text('{"date": "' + today + '", "words": 2500}', encoding="utf-8")
    return CheckinResponse(claimed=True, words=2500, message="签到成功，已领取 2500 字。")


def _reference_text() -> str:
    text = reference_cache.get("text", "")
    if not text.strip():
        raise HTTPException(status_code=400, detail="请先上传或粘贴参考文本")
    return text


def _style_result() -> Dict[str, Any]:
    if not reference_cache.get("style"):
        raise HTTPException(status_code=400, detail="请先点击文风分析")
    return reference_cache["style"]


def _dump_model(model: Any) -> Dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


def _infer_title(setting: Dict[str, Any]) -> str:
    inspiration = setting.get("inspiration") or setting.get("background") or setting.get("genre") or "未命名之书"
    title = str(inspiration).strip().splitlines()[0]
    for separator in ("，", "。", ",", ".", "！", "？"):
        title = title.split(separator)[0]
    return title[:12] or "未命名之书"


def _read_json(path: Path) -> Dict[str, Any]:
    try:
        import json

        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
