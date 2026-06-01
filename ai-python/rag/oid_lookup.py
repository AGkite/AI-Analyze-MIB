"""OID 解析：标准库 + 联网查询（Observium / DuckDuckGo）。"""
import re
from dataclasses import dataclass

import httpx

# 常见 SNMPv2-MIB / IF-MIB 等标准 OID（前缀匹配）
COMMON_OID_PREFIXES: dict[str, str] = {
    "1.3.6.1.2.1.1.1": "sysDescr — 系统描述",
    "1.3.6.1.2.1.1.2": "sysObjectID — 系统对象标识",
    "1.3.6.1.2.1.1.3": "sysUpTime — 系统运行时间",
    "1.3.6.1.2.1.1.4": "sysContact — 联系人",
    "1.3.6.1.2.1.1.5": "sysName — 系统名称",
    "1.3.6.1.2.1.1.6": "sysLocation — 物理位置",
    "1.3.6.1.2.1.1.7": "sysServices — 服务类型",
    "1.3.6.1.2.1.2.2.1.1": "ifIndex — 接口索引",
    "1.3.6.1.2.1.2.2.1.2": "ifDescr — 接口描述",
    "1.3.6.1.2.1.2.2.1.3": "ifType — 接口类型",
    "1.3.6.1.2.1.2.2.1.5": "ifSpeed — 接口速率",
    "1.3.6.1.2.1.2.2.1.8": "ifOperStatus — 接口运行状态",
    "1.3.6.1.2.1.2.2.1.10": "ifInOctets — 入站字节",
    "1.3.6.1.2.1.2.2.1.16": "ifOutOctets — 出站字节",
    "1.3.6.1.2.1.25.3.3.1.2": "hrProcessorLoad — CPU 负载",
    "1.3.6.1.2.1.25.2.3.1.5": "hrStorageSize — 存储大小",
    "1.3.6.1.2.1.25.2.3.1.6": "hrStorageUsed — 已用存储",
}

OBSERVIUM_OID_URL = "https://mibs.observium.org/oid/{oid}"
HTTP_TIMEOUT = 12.0


@dataclass
class OidLookupResult:
    oid: str
    name: str | None
    description: str | None
    source: str  # common | observium | web_search | unknown


def _match_common(oid: str) -> OidLookupResult | None:
    """最长前缀匹配标准 MIB OID。"""
    best_key = ""
    for prefix, label in COMMON_OID_PREFIXES.items():
        if (oid == prefix or oid.startswith(prefix + ".")) and len(prefix) > len(best_key):
            best_key = prefix
    if best_key:
        return OidLookupResult(
            oid=oid,
            name=COMMON_OID_PREFIXES[best_key].split("—")[0].strip(),
            description=COMMON_OID_PREFIXES[best_key],
            source="common",
        )
    return None


def _fetch_observium(oid: str) -> OidLookupResult | None:
    try:
        with httpx.Client(timeout=HTTP_TIMEOUT, follow_redirects=True) as client:
            resp = client.get(OBSERVIUM_OID_URL.format(oid=oid))
            if resp.status_code != 200:
                return None
            html = resp.text
    except Exception:
        return None

    title_m = re.search(r"<title[^>]*>([^<]+)</title>", html, re.I)
    title = title_m.group(1).strip() if title_m else None
    if not title or "404" in title.lower():
        return None

    desc_m = re.search(
        r'class="[^"]*description[^"]*"[^>]*>([^<]+)<',
        html,
        re.I,
    )
    description = desc_m.group(1).strip() if desc_m else title
    name = title.split("—")[0].strip() if "—" in title else title

    return OidLookupResult(
        oid=oid,
        name=name,
        description=description[:500],
        source="observium",
    )


def _search_web(oid: str) -> OidLookupResult | None:
    try:
        from duckduckgo_search import DDGS

        query = f"SNMP OID {oid} MIB definition"
        with DDGS() as ddgs:
            hits = list(ddgs.text(query, max_results=3))
        if not hits:
            return None
        snippets = []
        for h in hits:
            body = h.get("body") or h.get("snippet") or ""
            title = h.get("title") or ""
            if body or title:
                snippets.append(f"{title}: {body}".strip())
        if not snippets:
            return None
        return OidLookupResult(
            oid=oid,
            name=None,
            description="\n".join(snippets)[:800],
            source="web_search",
        )
    except Exception:
        return None


def lookup_oid(oid: str, *, use_web: bool = True) -> OidLookupResult:
    """解析单个 OID，依次尝试标准库、Observium、联网搜索。"""
    oid = oid.strip().rstrip(".")
    if oid.startswith("."):
        oid = oid[1:]

    common = _match_common(oid)
    if common:
        return common

    observium = _fetch_observium(oid)
    if observium:
        return observium

    if use_web:
        web = _search_web(oid)
        if web:
            return web

    return OidLookupResult(
        oid=oid,
        name=None,
        description="未能通过标准库或联网查询解析该 OID，请结合上传的私有 MIB 对照。",
        source="unknown",
    )


def lookup_oids_batch(
    oids: list[str],
    *,
    max_web: int = 30,
    use_web: bool = True,
) -> list[OidLookupResult]:
    """批量解析，限制联网次数以防过慢。"""
    results: list[OidLookupResult] = []
    web_count = 0

    for oid in oids:
        common = _match_common(oid)
        if common:
            results.append(common)
            continue

        observium = _fetch_observium(oid)
        if observium:
            results.append(observium)
            continue

        if use_web and web_count < max_web:
            web = _search_web(oid)
            web_count += 1
            if web:
                results.append(web)
                continue

        results.append(
            OidLookupResult(
                oid=oid,
                name=None,
                description="未解析（请参考私有 MIB）",
                source="unknown",
            )
        )
    return results


def format_lookup_report(results: list[OidLookupResult]) -> str:
    lines = ["# SNMP Walk OID 解析报告", ""]
    by_source: dict[str, list[OidLookupResult]] = {}
    for r in results:
        by_source.setdefault(r.source, []).append(r)

    labels = {
        "common": "标准公共 OID（本地库）",
        "observium": "Observium MIB 库",
        "web_search": "联网搜索解析",
        "unknown": "未识别 OID",
    }
    for source, label in labels.items():
        group = by_source.get(source, [])
        if not group:
            continue
        lines.append(f"## {label}（{len(group)} 个）")
        lines.append("")
        for r in group:
            name = r.name or "—"
            desc = (r.description or "").replace("\n", " ")
            lines.append(f"- **{r.oid}** — {name}: {desc[:200]}")
        lines.append("")

    return "\n".join(lines)
