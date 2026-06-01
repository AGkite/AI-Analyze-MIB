from langchain_classic.chains import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_openai import ChatOpenAI

from rag.config import (
    CHROMA_DIR,
    COLLECTION_NAME,
    EMBEDDING_MODEL,
    LLM_API_KEY,
    LLM_BASE_URL,
    LLM_MODEL,
    TOP_K,
)

SYSTEM_TEMPLATE = """你是私有代码库和 MIB / snmpwalk 智能分析助手。
请严格基于以下 [上下文资料] 与 [OID 联网解析] 回答用户问题。

要求：
1. 优先使用上下文与 OID 解析中的信息，不要编造 OID、函数名或代码逻辑
2. 对标准公共 OID（如 1.3.6.1.2.1.*）可结合 OID 解析说明
3. 对未识别的企业私有 OID，提示用户对照已上传的 MIB 文件
4. 若资料不足，明确说[资料中未找到相关信息]
5. 回答结构清晰，必要时引用来源文件名

上下文资料：
{context}

OID 联网解析（标准库 / Observium / 联网搜索）：
{oid_context}
"""

_embeddings: HuggingFaceEmbeddings | None = None
_vectorstore: Chroma | None = None
_chain = None


def _get_embeddings() -> HuggingFaceEmbeddings:
    global _embeddings
    if _embeddings is None:
        _embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    return _embeddings


def load_vectorstore() -> Chroma:
    """加载已有 Chroma 向量库。"""
    global _vectorstore
    if _vectorstore is not None:
        return _vectorstore

    if not CHROMA_DIR.exists():
        raise FileNotFoundError(
            f"向量库不存在: {CHROMA_DIR}\n请先上传文件并执行索引构建。"
        )

    _vectorstore = Chroma(
        persist_directory=str(CHROMA_DIR),
        embedding_function=_get_embeddings(),
        collection_name=COLLECTION_NAME,
    )
    return _vectorstore


def reset_cache() -> None:
    """入库后清除缓存，下次请求重新加载。"""
    global _embeddings, _vectorstore, _chain
    _embeddings = None
    _vectorstore = None
    _chain = None


def build_rag_chain(*, oid_context: str = "（无额外 OID 解析）"):
    """构建 RAG 链: Retrieval + Prompt + LLM。"""
    if not LLM_API_KEY:
        raise ValueError("未设置 MINIMAX_API_KEY, 请在 .env 中配置")

    vectorstore = load_vectorstore()
    retriever = vectorstore.as_retriever(search_kwargs={"k": TOP_K})

    llm = ChatOpenAI(
        model=LLM_MODEL,
        base_url=LLM_BASE_URL,
        api_key=LLM_API_KEY,
        temperature=0.7,
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_TEMPLATE.partial(oid_context=oid_context)),
        ("human", "{input}"),
    ])

    question_answer_chain = create_stuff_documents_chain(llm, prompt)
    return create_retrieval_chain(retriever, question_answer_chain)


def get_chain(*, oid_context: str = "（无额外 OID 解析）"):
    global _chain
    if _chain is None or oid_context != "（无额外 OID 解析）":
        return build_rag_chain(oid_context=oid_context)
    return _chain


def _load_oid_context() -> str:
    """加载最近生成的 OID 解析报告作为补充上下文。"""
    from rag.config import GENERATED_DIR

    if not GENERATED_DIR.exists():
        return "（无 snmpwalk OID 解析报告，请先上传 snmpwalk 文件）"

    reports = sorted(GENERATED_DIR.glob("oid-analysis-*.md"), reverse=True)
    if not reports:
        return "（无 snmpwalk OID 解析报告）"

    # 取最新一份，截断避免 token 过长
    text = reports[0].read_text(encoding="utf-8", errors="ignore")
    return text[:12000]


def ask(question: str, *, oid_context: str | None = None) -> dict:
    """单次问答，返回 answer 和 context。"""
    ctx = oid_context if oid_context is not None else _load_oid_context()
    chain = build_rag_chain(oid_context=ctx)
    return chain.invoke({"input": question})


def format_sources(docs: list) -> list[str]:
    seen: set[str] = set()
    sources: list[str] = []
    for doc in docs:
        source = doc.metadata.get("source", "unknown")
        if source not in seen:
            seen.add(source)
            sources.append(source)
    return sources


def chat_loop():
    """CLI 交互一问一答。"""
    print("--- 私有知识库助手（输入 退出 / exit / quit 结束）---")
    oid_ctx = _load_oid_context()
    chain = build_rag_chain(oid_context=oid_ctx)

    while True:
        try:
            question = input("\n你: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n--- 对话结束 ---")
            break

        if not question:
            continue
        if question.lower() in {"exit", "quit", "q", "退出", "再见"}:
            print("--- 对话结束 ---")
            break

        try:
            result = chain.invoke({"input": question})
            print(f"\n助手: {result['answer']}")
            print("\n--- 参考来源 ---")
            for source in format_sources(result.get("context", [])):
                print(f" - {source}")
        except Exception as e:
            print(f"\n请求失败: {e}")
