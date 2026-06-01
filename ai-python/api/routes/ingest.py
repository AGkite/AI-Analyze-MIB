import threading

from fastapi import APIRouter

from api.deps import get_ingest_status, run_ingest_background
from api.schemas import IngestStatus

router = APIRouter(prefix="/ingest", tags=["ingest"])


@router.post("", response_model=IngestStatus)
async def trigger_ingest():
    threading.Thread(target=run_ingest_background, daemon=True).start()
    return IngestStatus(status="queued", message="索引构建已启动")


@router.get("/status", response_model=IngestStatus)
async def ingest_status():
    s = get_ingest_status()
    return IngestStatus(
        status=s["status"],
        message=s["message"],
        document_count=s.get("document_count"),
    )
