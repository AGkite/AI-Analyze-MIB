from pathlib import Path

from fastapi import APIRouter

from rag.config import GENERATED_DIR, KNOWLEDGE_BASE_DIR, UPLOAD_DIR

router = APIRouter(prefix="/files", tags=["files"])


def _list_dir(base: Path, prefix: str) -> list[dict]:
    if not base.exists():
        return []
    items = []
    for p in sorted(base.rglob("*")):
        if p.is_file():
            rel = p.relative_to(KNOWLEDGE_BASE_DIR).as_posix()
            items.append({
                "name": p.name,
                "path": rel,
                "kind": prefix,
                "size": p.stat().st_size,
            })
    return items


@router.get("")
async def list_files():
    return {
        "mib": _list_dir(KNOWLEDGE_BASE_DIR / "mib", "mib"),
        "snmpwalk": _list_dir(KNOWLEDGE_BASE_DIR / "snmpwalk", "snmpwalk"),
        "generated": _list_dir(GENERATED_DIR, "generated"),
        "uploads": _list_dir(UPLOAD_DIR, "uploads") if UPLOAD_DIR.exists() else [],
    }
