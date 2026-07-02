from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class StyleAnalysis(BaseModel):
    style: str = ""
    perspective: str = ""
    pace: str = ""
    emotion: str = ""
    narrative_mode: str = ""
    writing_rules: List[str] = Field(default_factory=list)


class UserSetting(BaseModel):
    genre: str = ""
    location: str = ""
    background: str = ""
    characters: str = ""
    inspiration: str = ""
    writing_style: str = ""
    template: str = ""
    public_library: str = ""


class GeneratePlotRequest(UserSetting):
    world: Optional[str] = None


class GenerateNovelRequest(UserSetting):
    world: str
    plot: str


class ReferenceUploadRequest(BaseModel):
    text: str


class GenerationResponse(BaseModel):
    content: str
    prompt: Optional[str] = None


class CoverRequest(UserSetting):
    title: str = ""
    subtitle: str = ""


class CoverResponse(BaseModel):
    title: str
    svg: str


class DraftPackageResponse(BaseModel):
    outline: str
    cover: CoverResponse
    novel: str
    directions: List[str]


class TextPayload(BaseModel):
    text: str
    title: str = ""


class InfoQuery(BaseModel):
    query: str
    platform: str = ""


class DirectionRequest(UserSetting):
    world: str = ""
    plot: str = ""


class ChapterIntelResponse(BaseModel):
    main_line: List[str]
    side_line: List[str]
    romance_line: List[str]
    faction_line: List[str]
    risks: List[str]


class HistoryRecord(BaseModel):
    kind: str
    title: str
    content: str
    created_at: str


class CheckinResponse(BaseModel):
    claimed: bool
    words: int
    message: str


class CacheState(BaseModel):
    has_reference: bool
    has_style: bool
    reference_length: int
    style: Optional[Dict[str, Any]] = None
