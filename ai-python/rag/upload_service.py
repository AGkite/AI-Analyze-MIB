"""处理网页上传的 MIB / snmpwalk 文件。"""
from datetime import datetime, timezone
from pathlib import Path

from rag.config import GENERATED_DIR, KNOWLEDGE_BASE_DIR, SUPPORTED_SUFFIXES, UPLOAD_DIR
from rag.oid_lookup import format_lookup_report, lookup_oids_batch
from rag.snmpwalk_parser import parse_snmpwalk_text, summarize_walk

SNMPWALK_SUFFIXES = {".snmpwalk", ".walk", ".txt", ".out", ".log"}
MIB_SUFFIXES = {".mib", ".my", ".smi", ".txt"}


def _ensure_dirs() -> None:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    (KNOWLEDGE_BASE_DIR / "mib").mkdir(parents=True, exist_ok=True)
    (KNOWLEDGE_BASE_DIR / "snmpwalk").mkdir(parents=True, exist_ok=True)
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)


def _looks_like_snmpwalk(content: bytes) -> bool:
    text = content[:4000].decode("utf-8", errors="ignore")
    return bool(parse_snmpwalk_text(text))


def classify_upload(filename: str, content: bytes | None = None) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix in {".mib", ".my", ".smi"}:
        return "mib"
    if suffix in SNMPWALK_SUFFIXES or "snmpwalk" in filename.lower() or "walk" in filename.lower():
        return "snmpwalk"
    if content and _looks_like_snmpwalk(content):
        return "snmpwalk"
    if suffix in SUPPORTED_SUFFIXES:
        return "other"
    raise ValueError(f"不支持的文件类型: {suffix}")


def save_upload(filename: str, content: bytes) -> dict:
    """保存上传文件，snmpwalk 会生成 OID 解析报告。"""
    _ensure_dirs()
    kind = classify_upload(filename, content)
    safe_name = Path(filename).name
    target_dir = UPLOAD_DIR / kind
    target_dir.mkdir(parents=True, exist_ok=True)
    dest = target_dir / safe_name
    dest.write_bytes(content)

    kb_rel = None
    if kind == "mib":
        kb_dest = KNOWLEDGE_BASE_DIR / "mib" / safe_name
        kb_dest.write_bytes(content)
        kb_rel = f"mib/{safe_name}"
    elif kind == "snmpwalk":
        kb_dest = KNOWLEDGE_BASE_DIR / "snmpwalk" / safe_name
        kb_dest.write_bytes(content)
        kb_rel = f"snmpwalk/{safe_name}"
        report_path = _analyze_snmpwalk(kb_dest, safe_name)
        return {
            "filename": safe_name,
            "kind": kind,
            "path": str(dest),
            "knowledge_path": kb_rel,
            "oid_report": str(report_path) if report_path else None,
        }

    return {
        "filename": safe_name,
        "kind": kind,
        "path": str(dest),
        "knowledge_path": kb_rel,
        "oid_report": None,
    }


def _analyze_snmpwalk(file_path: Path, original_name: str) -> Path | None:
    text = file_path.read_text(encoding="utf-8", errors="ignore")
    entries = parse_snmpwalk_text(text)
    if not entries:
        return None

    oids = [e.oid for e in entries]
    lookups = lookup_oids_batch(oids, use_web=True)
    report = format_lookup_report(lookups)
    walk_summary = summarize_walk(entries)

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    report_name = f"oid-analysis-{original_name}-{ts}.md"
    report_path = GENERATED_DIR / report_name

    full_doc = (
        f"# Snmpwalk 分析: {original_name}\n\n"
        f"## Walk 原始摘要\n\n{walk_summary}\n\n"
        f"{report}\n"
    )
    report_path.write_text(full_doc, encoding="utf-8")
    return report_path
