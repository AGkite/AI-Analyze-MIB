from pathlib import Path
from langchain_core.documents import Document
from rag.config import KNOWLEDGE_BASE_DIR, SUPPORTED_SUFFIXES

def _doc_type(path: Path) -> str:
    """根据后缀判断文档类型，供 metadata 过滤使用。"""
    suffix = path.suffix.lower()
    if suffix in {".mib", ".my", ".smi"}:
        return "mib"
    if suffix in {".snmpwalk", ".walk", ".out", ".log"}:
        return "snmpwalk"
    if suffix in {".py", ".java"}:
        return "code"
    if suffix in {".txt", ".md"}:
        return "doc"
    return "other"

def load_knowledge_base(base_dir: Path | None = None) -> list[Document]:
    """
    扫描 knowledge-base 目录，加载所有支持的文件。

    返回 LangChain Document 列表:
    - page_content: 文件正文
    - metadata: 来源、类型等
    """
    root = base_dir or KNOWLEDGE_BASE_DIR
    if not root.exists():
        raise FileNotFoundError(f"知识库目录不存在: {root}")
    
    documents: list[Document] = []

    for file_path in sorted(root.rglob("*")):
        if not file_path.is_file():
            continue
        if file_path.suffix.lower() not in SUPPORTED_SUFFIXES:
            continue

        text = file_path.read_text(encoding="utf-8", errors="ignore")
        if not text.strip():
            continue

        rel_path = file_path.relative_to(root).as_posix()
        documents.append(
            Document(
                page_content=text,
                metadata={
                    "source": rel_path,
                    "doc_type": _doc_type(file_path),
                    "file_name": file_path.name,
                },
            )
        )
    return documents

