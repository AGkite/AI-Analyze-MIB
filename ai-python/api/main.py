"""FastAPI 应用入口。运行: uvicorn api.main:app --reload --host 0.0.0.0 --port 8000"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import chat, files, ingest, upload
from api.schemas import HealthResponse
from rag.config import API_HOST, API_PORT, CHROMA_DIR, CORS_ORIGINS, LLM_API_KEY


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="AI-Analyze-MIB API",
    description="MIB / snmpwalk 上传分析与 RAG 问答",
    version="1.0.0",
    lifespan=lifespan,
)

origins = [o.strip() for o in CORS_ORIGINS.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router, prefix="/api")
app.include_router(ingest.router, prefix="/api")
app.include_router(files.router, prefix="/api")
app.include_router(chat.router, prefix="/api")


@app.get("/api/health", response_model=HealthResponse)
async def health():
    return HealthResponse(
        status="ok",
        vectorstore_ready=CHROMA_DIR.exists(),
        minimax_configured=bool(LLM_API_KEY),
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api.main:app", host=API_HOST, port=API_PORT, reload=True)
