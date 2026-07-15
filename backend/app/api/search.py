import re
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.db import get_db
from app.models.history import SearchHistory
from app.models.source import Source, Entry
from app.integrations import meilisearch_client as meili
from app.integrations.searxng_client import searxng_client
from app.integrations.opencode import llm_json, get_embedding
from app.schemas import ScanRequest, ScanResult

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
        context = "\n".join(f"- {r.get('title', '')}: {r.get('content', '')[:100]}" for r in tops)
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

    l1_results = await meili.search_entries(keyword, limit=20, filters='source_type IN ["R", "S"]')
    l1_count = len(l1_results)

    l2_results = []
    if l1_count < 10:
        l2_results = await meili.search_cases(keyword, limit=10)

    searxng_results = []
    if not req.skip_searxng and (l1_count + len(l2_results)) < 15:
        try:
            searxng_results = await searxng_client.search(keyword, limit=15)
        except Exception as e:
            logger.warning(f"SearXNG search failed: {e}")

    all_results = l1_results + l2_results
    clustered = await auto_cluster(all_results, keyword) if len(all_results) >= 3 else None
    report = await generate_report(keyword, strength, all_results)

    history = SearchHistory(
        keyword=keyword,
        result_count=len(all_results) + len(searxng_results),
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
        l1_results=l1_results,
        l2_results=l2_results,
        searxng_results=searxng_results,
        total=len(all_results) + len(searxng_results),
        clustered=clustered,
        report=report,
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