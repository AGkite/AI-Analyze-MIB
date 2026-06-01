from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from rag.config import (
    CHROMA_DIR,
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    COLLECTION_NAME,
    EMBEDDING_MODEL,
    KNOWLEDGE_BASE_DIR,
)
from rag.loaders import load_knowledge_base

def build_vectorsstore():
    """完整入库流程：加载 -> 切分 -> embedding -> 写入Chroma。"""
    print(f"1/4 加载知识库: {KNOWLEDGE_BASE_DIR}")
    documents = load_knowledge_base()
    if not documents:
        raise ValueError("知识库为空，请先往 knowledge-base 目录添加文档。")

    print(f"    共加载 {len(documents)} 个文件")

    print(f"2/4 文本切分 (size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP}) ")
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", " ", ""],
    )
    chunks = splitter.split_documents(documents)
    print(f"    切分后共 {len(chunks)} 个段落")

    print(f"3/4 加载 Embedding 模型: {EMBEDDING_MODEL}")
    print("    (首次运行会下载模型，请耐心等待)")
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)

    print(f"4/4 写入 Chroma: {CHROMA_DIR}")

    CHROMA_DIR.mkdir(parents=True, exist_ok=True)

    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=str(CHROMA_DIR),
        collection_name=COLLECTION_NAME,
    )

    print("入库完成！")
    return vectorstore

if __name__ == "__main__":
    build_vectorsstore()