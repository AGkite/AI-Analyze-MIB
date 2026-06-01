import re

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from api.schemas import ChatRequest, ChatResponse, OidLookupRequest
from rag.assistant import _load_oid_context, ask, format_sources
from rag.config import LLM_API_KEY
from rag.oid_lookup import lookup_oid

router = APIRouter(tags=["chat"])

OID_IN_TEXT_RE = re.compile(r"\b(?:\d+\.){4,}\d+(?:\.\d+)*\b")


def _extract_oids(text: str) -> list[str]:
    return list(dict.fromkeys(OID_IN_TEXT_RE.findall(text)))


def _enrich_oid_context(message: str, *, use_web: bool) -> tuple[str, list[dict]]:
    base = _load_oid_context()
    oids = _extract_oids(message)
    if not oids:
        return base, []

    extra_lines = []
    lookups: list[dict] = []
    for oid in oids[:5]:
        r = lookup_oid(oid, use_web=use_web)
        lookups.append({
            "oid": r.oid,
            "name": r.name,
            "description": r.description,
            "source": r.source,
        })
        extra_lines.append(
            f"- {r.oid} [{r.source}]: {r.name or '—'} — {(r.description or '')[:300]}"
        )

    enriched = base + "\n\n## 本次问题涉及 OID 实时查询\n" + "\n".join(extra_lines)
    return enriched[:14000], lookups


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    if not LLM_API_KEY:
        raise HTTPException(500, "未配置 MINIMAX_API_KEY")

    try:
        oid_ctx, oid_lookups = _enrich_oid_context(
            req.message, use_web=req.lookup_oid_online
        )
        result = ask(req.message, oid_context=oid_ctx)
    except FileNotFoundError as e:
        raise HTTPException(400, str(e)) from e
    except ValueError as e:
        raise HTTPException(500, str(e)) from e
    except Exception as e:
        raise HTTPException(500, f"问答失败: {e}") from e

    return ChatResponse(
        answer=result.get("answer", ""),
        sources=format_sources(result.get("context", [])),
        oid_lookups=oid_lookups,
    )


@router.post("/chat/stream")
async def chat_stream(req: ChatRequest):
    if not LLM_API_KEY:
        raise HTTPException(500, "未配置 MINIMAX_API_KEY")

    async def event_generator():
        import json

        try:
            oid_ctx, oid_lookups = _enrich_oid_context(
                req.message, use_web=req.lookup_oid_online
            )
            result = ask(req.message, oid_context=oid_ctx)
            answer = result.get("answer", "")
            chunk_size = 40
            for i in range(0, len(answer), chunk_size):
                yield f"data: {json.dumps(answer[i:i + chunk_size], ensure_ascii=False)}\n\n"

            sources = format_sources(result.get("context", []))
            yield f"event: sources\ndata: {json.dumps(sources, ensure_ascii=False)}\n\n"
            if oid_lookups:
                yield f"event: oid_lookups\ndata: {json.dumps(oid_lookups, ensure_ascii=False)}\n\n"
            yield "event: done\ndata: [DONE]\n\n"
        except Exception as e:
            yield f"event: error\ndata: {str(e)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/oid/lookup")
async def oid_lookup(req: OidLookupRequest):
    r = lookup_oid(req.oid.strip(), use_web=True)
    return {
        "oid": r.oid,
        "name": r.name,
        "description": r.description,
        "source": r.source,
    }
