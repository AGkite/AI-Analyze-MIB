"""解析 snmpwalk 输出文件，提取 OID 与取值。"""
import re
from dataclasses import dataclass

# 典型行: .1.3.6.1.2.1.1.3.0 = Timeticks: (123) 0:00:01.23
# 或: iso.3.6.1.2.1.1.3.0 = ...
OID_LINE_RE = re.compile(
    r"^(?:\.|iso\.)?(?P<oid>[\d.]+)\s*=\s*(?P<value>.+)$",
    re.MULTILINE,
)


@dataclass
class WalkEntry:
    oid: str
    value: str


def normalize_oid(oid: str) -> str:
    """统一为以 1. 开头的数字 OID。"""
    oid = oid.strip().strip(".")
    if oid.startswith("iso."):
        oid = oid[4:]
    if not oid.startswith("1."):
        if oid.startswith("."):
            oid = oid[1:]
    return oid


def parse_snmpwalk_text(text: str) -> list[WalkEntry]:
    entries: list[WalkEntry] = []
    seen: set[str] = set()

    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        m = OID_LINE_RE.match(line)
        if not m:
            continue
        oid = normalize_oid(m.group("oid"))
        if not oid or oid in seen:
            continue
        seen.add(oid)
        entries.append(WalkEntry(oid=oid, value=m.group("value").strip()))

    return entries


def summarize_walk(entries: list[WalkEntry], max_lines: int = 200) -> str:
    """生成可写入知识库的文本摘要。"""
    lines = [f"共 {len(entries)} 个唯一 OID", ""]
    for i, e in enumerate(entries[:max_lines]):
        lines.append(f"- {e.oid} = {e.value[:120]}")
    if len(entries) > max_lines:
        lines.append(f"... 另有 {len(entries) - max_lines} 条未列出")
    return "\n".join(lines)
