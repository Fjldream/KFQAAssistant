from typing import Literal

from pydantic import BaseModel, Field, field_validator


class ChatHistoryMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=1200)

    @field_validator("content")
    @classmethod
    def strip_content(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("历史消息不能为空")
        return stripped


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000)
    conversation_summary: str = Field(default="", max_length=2000)
    conversation_turn_count: int = Field(default=0, ge=0, le=10000)
    recent_messages: list[ChatHistoryMessage] = Field(default_factory=list, max_length=8)

    @field_validator("question")
    @classmethod
    def strip_question(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("问题不能为空")
        return stripped

    @field_validator("conversation_summary")
    @classmethod
    def strip_conversation_summary(cls, value: str) -> str:
        return value.strip()


class SourceSnippet(BaseModel):
    title: str
    source_path: str
    snippet: str
    evidence_ids: list[str] = Field(default_factory=list)
    images: list[str] = Field(default_factory=list)
    score: float | None = None


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceSnippet] = Field(default_factory=list)
    conversation_summary: str = ""
    standalone_question: str = ""
