from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    lookup_oid_online: bool = Field(
        default=True,
        description="问题中含 OID 时是否联网查询",
    )


class ChatResponse(BaseModel):
    answer: str
    sources: list[str] = []
    oid_lookups: list[dict] = []


class IngestStatus(BaseModel):
    status: str
    message: str
    document_count: int | None = None


class UploadResponse(BaseModel):
    files: list[dict]
    message: str


class OidLookupRequest(BaseModel):
    oid: str


class HealthResponse(BaseModel):
    status: str
    vectorstore_ready: bool
    minimax_configured: bool
