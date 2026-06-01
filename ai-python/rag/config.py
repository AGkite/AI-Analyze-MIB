import os
from pathlib import Path
from dotenv import load_dotenv

# ai-python 目录
BASE_DIR = Path(__file__).parent.parent
load_dotenv(BASE_DIR / ".env")

# 原始资料目录
KNOWLEDGE_BASE_DIR = BASE_DIR / "knowledge-base"

# Chroma 数据库目录
CHROMA_DIR = BASE_DIR / "chroma-data"
COLLECTION_NAME = "qa_private_kb"

# Embedding 模型 (本地)
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-zh-v1.5")

# LLM (MinMax OpenAI 兼容)
LLM_BASE_URL = os.getenv("MINIMAX_BASE_URL", "https://api.minimaxi.com/v1")
LLM_API_KEY = os.getenv("MINIMAX_API_KEY", "")
LLM_MODEL = os.getenv("MINIMAX_MODEL", "MiniMax-M2.7")

# 切分与检索
CHUNK_SIZE = int(os.getenv("RAG_CHUNK_SIZE", "800"))
CHUNK_OVERLAP = int(os.getenv("RAG_CHUNK_OVERLAP", "120"))
TOP_K = int(os.getenv("RAG_TOP_K", "4"))

# 支持的文件类型
SUPPORTED_SUFFIXES = {".mib", ".txt", ".md", ".py", ".java", ".yml", ".yaml", ".json"}




