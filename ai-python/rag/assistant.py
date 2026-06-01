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

SYSTEM_TEMPLATE = """你是私有代码库和 MIB 文档智能分析助手。
请严格基于以下 [上下文资料] 回答用户问题。如果无法回答，请礼貌告知用户 "对不起，我无法回答这个问题。

要求：
1. 只使用上下文中的信息，不要编造 OID、函数名或代码逻辑
2. 如果上下文不足以回答，请明确说[资料中未找到相关信息]
3. 回答尽量结构清晰，必要时引用来源文件名
4. 你是 MiniMax 驱动的分析助手

上下文资料：
{context}
"""

def _get_embeddings():
    return HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)

def load_vectorstore():
    """加载已有 Chroma 向量库。"""
    if not CHROMA_DIR.exists():
        raise FileNotFoundError(f"向量库不存在: {CHROMA_DIR}\n请先运行: python rag_assistant.py ingest")

    return Chroma(
        persist_directory=str(CHROMA_DIR),
        embedding_function=_get_embeddings(),
        collection_name=COLLECTION_NAME,
    )

def build_rag_chain():
    """构建 RAG 链: Retrieval + Prompt + LLM。"""
    if not LLM_API_KEY:
        raise ValueError("未设置 MINIMAX_API_KEY, 请在 .env 中配置")
    
    vectorstore = load_vectorstore()
    retriever = vectorstore.as_retriever(search_kwargs={"k": TOP_K})

    llm = ChatOpenAI(
        model=LLM_MODEL,
        base_url=LLM_BASE_URL,
        api_key=LLM_API_KEY,
        temperature=1.0,
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_TEMPLATE),
        ("human", "{input}")
    ])

    # 把检索到的 docs 塞进 prompt 的 {context}
    question_answer_chain = create_stuff_documents_chain(llm, prompt)

    # 串联：先检索，再回答
    return create_retrieval_chain(retriever, question_answer_chain)


def ask(question: str) -> dict:
    """单次问答，返回 answer 和 context。"""
    chain = build_rag_chain()
    return chain.invoke({"input": question})

def chat_loop():
    """交互一问一答。"""
    print("--- 私有知识库助手（输入 退出 / exit / quit 结束）---")
    chain = build_rag_chain()

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
            seen = set()
            for doc in result.get("context", []):
                source = doc.metadata.get("source", "unknown")
                if source in seen:
                    print(f" - {source}")
                    seen.add(source)
        except Exception as e:
            print(f"\n请求失败: {e}")

