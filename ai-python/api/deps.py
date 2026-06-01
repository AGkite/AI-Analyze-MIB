"""应用级状态与后台任务。"""
import threading

_ingest_lock = threading.Lock()
_ingest_status = {
    "status": "idle",
    "message": "尚未构建索引",
    "document_count": None,
}


def get_ingest_status() -> dict:
    return dict(_ingest_status)


def set_ingest_status(status: str, message: str, document_count: int | None = None) -> None:
    _ingest_status["status"] = status
    _ingest_status["message"] = message
    if document_count is not None:
        _ingest_status["document_count"] = document_count


def run_ingest_background() -> None:
    if not _ingest_lock.acquire(blocking=False):
        set_ingest_status("running", "索引构建正在进行中…")
        return

    try:
        set_ingest_status("running", "正在扫描知识库并构建向量索引…")
        from rag.ingest import build_vectorsstore

        build_vectorsstore()
        from rag.loaders import load_knowledge_base

        docs = load_knowledge_base()
        set_ingest_status(
            "done",
            "索引构建完成",
            document_count=len(docs),
        )
    except Exception as e:
        set_ingest_status("error", str(e))
    finally:
        _ingest_lock.release()
