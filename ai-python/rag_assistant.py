import argparse
import sys

def main():
    parser = argparse.ArgumentParser(description="私有代码库 / MIB 文档 RAG 助手")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("ingest", help="扫描 knowledge-base 并写入 Chroma 向量库")
    sub.add_parser("chat", help="交互式问答")

    ask_parser = sub.add_parser("ask", help="单次问答")
    ask_parser.add_argument("question", type=str, help="你的问题")

    args = parser.parse_args()

    if args.command == "ingest":
        from rag.ingest import build_vectorsstore
        build_vectorsstore()

    elif args.command == "chat":
        from rag.assistant import chat_loop
        chat_loop()

    elif args.command == "ask":
        from rag.assistant import ask
        result = ask(args.question)
        print(result["answer"])
        print("\n--- 参考来源 ---")
        for doc in result.get("context", []):
            print(f" - {doc.metadata.get('source')}")

    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()