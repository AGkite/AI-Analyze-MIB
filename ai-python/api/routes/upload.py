from fastapi import APIRouter, File, HTTPException, Query, UploadFile

from api.deps import run_ingest_background, set_ingest_status
from api.schemas import UploadResponse
from rag.upload_service import save_upload

router = APIRouter(prefix="/upload", tags=["upload"])

MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB


@router.post("", response_model=UploadResponse)
async def upload_files(
    files: list[UploadFile] = File(...),
    auto_ingest: bool = Query(True),
):
    if not files:
        raise HTTPException(400, "请至少上传一个文件")

    saved: list[dict] = []
    for f in files:
        content = await f.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(400, f"文件过大: {f.filename}（上限 20MB）")
        if not f.filename:
            continue
        try:
            saved.append(save_upload(f.filename, content))
        except ValueError as e:
            raise HTTPException(400, str(e)) from e

    msg = f"已上传 {len(saved)} 个文件"
    if auto_ingest:
        set_ingest_status("queued", "已加入索引队列…")
        import threading

        threading.Thread(target=run_ingest_background, daemon=True).start()
        msg += "，正在后台构建索引"

    return UploadResponse(files=saved, message=msg)
