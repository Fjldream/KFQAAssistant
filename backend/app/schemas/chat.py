from pydantic import BaseModel, Field, field_validator


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000)

    @field_validator("question")
    @classmethod
    def strip_question(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("问题不能为空")
        return stripped


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
