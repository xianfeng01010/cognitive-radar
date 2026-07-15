import re
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db import get_db
from app.models.history import SearchHistory
from app.models.source import Source
from app.integrations import meilisearch_client as meili
from app.integrations.searxng_client import searxng_client
from app.integrations.opencode import llm_json
from app.schemas import ScanRequest, ScanResult, CardItem, CardDetailRequest, CardDetailResponse

logger = logging.getLogger(__name__)
router = APIRouter()

STRONG_PATTERNS = [
    r"如何|怎么|怎样|方法|经验|教程|指南|步骤",
    r"how to|guide|tutorial|experience|method|step",
    r"选择.*还是|应该.*吗|值不值得|对比|比较",
]
WEAK_PATTERNS = [
    r"哪里|什么好吃|好玩|天气|怎么样|好看吗",
    r"今天|明天|本周|周末|现在",
    r"stock|price|今日|行情",
]


def classify_strength(keyword: str) -> str:
    if any(re.search(p, keyword, re.IGNORECASE) for p in STRONG_PATTERNS):
        return "strong"
    if any(re.search(p, keyword, re.IGNORECASE) for p in WEAK_PATTERNS):
        return "weak"
    return "medium"


async def auto_cluster(results: list[dict], keyword: str) -> dict | None:
    if len(results) < 3:
        return None
    try:
        titles = [r.get("title", "") for r in results[:20]]
        prompt = f"搜索关键词：{keyword}\n\n以下是一组搜索结果标题：\n" + "\n".join(f"{i+1}. {t}" for i, t in enumerate(titles))
        prompt += "\n\n请将这些结果聚类，返回JSON格式：{\"clusters\": [{\"label\": \"标签\", \"items\": [序号列表]}]}"
        result = await llm_json(prompt, system="你是一个信息聚类助手，只返回JSON。", max_tokens=800)
        return result
    except Exception as e:
        logger.warning(f"Clustering failed: {e}")
        return None


async def generate_report(keyword: str, strength: str, results: list[dict]) -> dict | None:
    if strength == "weak" or len(results) == 0:
        return None
    try:
        tops = results[:5]
        context = "\n".join(f"- {r.get('title', '')}: {(r.get('content_preview', '') or '')[:100]}" for r in tops)
        if strength == "strong":
            prompt = f"搜索关键词：{keyword}\n\n以下是相关搜索结果：\n{context}\n\n请生成一份结构化报告，包含：1) 摘要 2) 关键发现 3) 人物/机构 4) 时间线 5) 结论。返回JSON格式。"
        else:
            prompt = f"搜索关键词：{keyword}\n\n以下是相关搜索结果：\n{context}\n\n请生成简短摘要和关键发现。返回JSON格式：{{\"summary\": \"\", \"key_findings\": []}}。"
        return await llm_json(prompt, system="你是一个信息分析助手，只返回JSON。", max_tokens=1500)
    except Exception as e:
        logger.warning(f"Report generation failed: {e}")
        return None


@router.post("/scan", response_model=ScanResult)
async def scan(req: ScanRequest, db: AsyncSession = Depends(get_db)):
    keyword = req.keyword
    strength = classify_strength(keyword)
    page = req.page
    page_size = req.page_size

    l1_limit = page_size * 2
    l1_results = await meili.search_entries(keyword, limit=l1_limit, filters='source_type IN ["R", "S"]')
    l1_count = len(l1_results)

    l2_results = []
    if l1_count < 10:
        l2_results = await meili.search_cases(keyword, limit=10)

    searxng_results = []
    if not req.skip_searxng:
        try:
            searxng_results = await searxng_client.search(keyword, limit=page_size * 3, time_range="month")
        except Exception as e:
            logger.warning(f"SearXNG search failed: {e}")

    all_cards: list[CardItem] = []

    for r in l1_results:
        all_cards.append(CardItem(
            id=str(r.get("id", "")),
            title=r.get("title", ""),
            content_preview=(r.get("content", "") or "")[:500],
            source=r.get("source_id", ""),
            url=r.get("url", ""),
            cache_level="L1",
            trust_score=float(r.get("trust_score", 50.0)),
            published_date=r.get("published_at", "") or "",
            thumbnail="",
            engines=[],
        ))

    for r in l2_results:
        all_cards.append(CardItem(
            id=str(r.get("id", "")),
            title=r.get("title", ""),
            content_preview=(r.get("outcome", "") or r.get("content", "") or "")[:500],
            source=r.get("source_url", ""),
            url=r.get("source_url", r.get("url", "")),
            cache_level="L2",
            trust_score=float(r.get("trust_score", 50.0)),
            engines=[],
        ))

    for r in searxng_results:
        pd = r.get("publishedDate") or ""
        all_cards.append(CardItem(
            id=f"searxng-{r.get('url', '')[:32]}",
            title=r.get("title", ""),
            content_preview=(r.get("content", "") or "")[:500],
            source=r.get("engine", ""),
            url=r.get("url", ""),
            cache_level="SearXNG",
            trust_score=30.0,
            published_date=str(pd) if pd else "",
            thumbnail=r.get("img_src") or r.get("thumbnail_src") or "",
            engines=r.get("engines", []),
        ))

    total = len(all_cards)
    total_pages = max(1, (total + page_size - 1) // page_size)
    start = (page - 1) * page_size
    cards = all_cards[start:start + page_size]

    # Convert CardItem to dict for LLM helper functions that use .get()
    all_cards_dicts = [c.model_dump() for c in all_cards[:20]]
    clustered = await auto_cluster(all_cards_dicts, keyword) if total >= 3 else None
    report = await generate_report(keyword, strength, all_cards_dicts[:5])

    history = SearchHistory(
        keyword=keyword,
        result_count=total,
        search_strength=strength,
    )
    db.add(history)
    await db.commit()

    if searxng_results:
        for r in searxng_results[:3]:
            existing = await db.execute(
                select(Source).where(Source.url == r.get("url", ""))
            )
            src = existing.scalar_one_or_none()
            if not src and r.get("url"):
                src = Source(
                    name=r.get("title", "")[:255],
                    url=r["url"],
                    source_type="S",
                    cache_level="L2",
                    trust_score=30.0,
                    added_by_search=keyword,
                )
                db.add(src)
        await db.commit()

    return ScanResult(
        keyword=keyword,
        strength=strength,
        cards=cards,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        clustered=clustered,
        report=report,
    )


# --- Local template extraction (zero LLM, zero tokens, instant) ---

_SENTENCE_SPLIT = re.compile(r'[。！？\n.!?]')
_CN_NAME = re.compile(r'[\u4e00-\u9fa5]{2,4}(?:公司|大学|研究所|研究院|机构|集团|实验室|团队|组织|政府|部门)')
_EN_NAME = re.compile(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2}\b')
_EN_ORG = re.compile(r'\b[A-Z][A-Za-z]+(?:\s(?:Inc|Corp|Ltd|LLC|GmbH|Co|Group|Labs|Research|Institute|University|Foundation|Association))\b')
_DATE_PATTERNS = re.compile(r'(\d{4}年\d{1,2}月\d{1,2}日|\d{4}-\d{1,2}-\d{1,2}|\d{4}年\d{1,2}月|\d{4}年|今年|去年|上个月|本周|近日|近期|最近)')


def _split_sentences(text: str) -> list[str]:
    parts = _SENTENCE_SPLIT.split(text)
    return [p.strip() for p in parts if p.strip() and len(p.strip()) > 5]


def _extract_tldr(content: str, title: str) -> str:
    sentences = _split_sentences(content)
    if sentences:
        return sentences[0][:80]
    return title[:80]


def _extract_key_findings(content: str, keyword: str, max_n: int = 3) -> list[str]:
    sentences = _split_sentences(content)
    if not sentences:
        return []
    kw_lower = keyword.lower()
    scored = []
    for s in sentences:
        score = 0
        if kw_lower in s.lower():
            score += 2
        if any(w in s for w in keyword.split() if len(w) > 1):
            score += 1
        if len(s) > 15:
            score += 1
        if score > 0:
            scored.append((score, s))
    if not scored:
        return sentences[:max_n]
    scored.sort(key=lambda x: x[0], reverse=True)
    return [s for _, s in scored[:max_n]]


def _extract_entities(content: str, title: str) -> list[str]:
    text = f"{title} {content}"
    entities = set()
    for m in _CN_NAME.finditer(text):
        entities.add(m.group())
    for m in _EN_NAME.finditer(text):
        entities.add(m.group())
    for m in _EN_ORG.finditer(text):
        entities.add(m.group())
    return list(entities)[:8]


def _extract_timeline(content: str) -> list[str]:
    sentences = _split_sentences(content)
    timeline = []
    for s in sentences:
        if _DATE_PATTERNS.search(s):
            timeline.append(s[:100])
    return timeline[:5]


def _extract_conclusion(content: str) -> str:
    sentences = _split_sentences(content)
    if not sentences:
        return ""
    conclusion_keywords = ["综上", "因此", "总之", "可见", "由此", "结论", "启示", "意味着", "表明", "说明"]
    for s in reversed(sentences):
        if any(kw in s for kw in conclusion_keywords):
            return s[:120]
    return sentences[-1][:120] if sentences else ""


@router.post("/detail", response_model=CardDetailResponse)
async def get_card_detail(req: CardDetailRequest):
    content = req.content or ""
    title = req.title or ""

    return CardDetailResponse(
        title=title,
        tldr=_extract_tldr(content, title),
        key_findings=_extract_key_findings(content, req.source or title),
        key_entities=_extract_entities(content, title),
        timeline=_extract_timeline(content),
        conclusion=_extract_conclusion(content),
        source_url=req.url,
    )


@router.get("/strength")
async def get_strength(keyword: str):
    return {"keyword": keyword, "strength": classify_strength(keyword)}


@router.get("/history")
async def search_history(limit: int = 20, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(SearchHistory).order_by(SearchHistory.created_at.desc()).limit(limit)
    )
    rows = result.scalars().all()
    return {"history": [{"id": str(r.id), "keyword": r.keyword, "result_count": r.result_count, "strength": r.search_strength, "created_at": r.created_at.isoformat() if r.created_at else None} for r in rows]}