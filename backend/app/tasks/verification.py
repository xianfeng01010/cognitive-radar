import asyncio
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


async def _verify_item(buffer_item_id: str):
    from app.db import create_celery_engine
    from app.models.buffer import BufferItem, Verification
    from app.models.source import Entry
    from app.integrations.searxng_client import searxng_client
    from app.integrations.opencode import llm_json
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    eng = create_celery_engine()
    session_factory = async_sessionmaker(eng, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as db:
        result = await db.execute(
            select(BufferItem).where(BufferItem.id == buffer_item_id)
        )
        item = result.scalar_one_or_none()
        if not item:
            await eng.dispose()
            return {"status": "not_found"}

        entry_result = await db.execute(
            select(Entry).where(Entry.id == item.entry_id)
        )
        entry = entry_result.scalar_one_or_none()
        if not entry:
            await eng.dispose()
            return {"status": "no_entry"}

        keywords = entry.keywords if entry.keywords else [entry.title[:50]]
        all_results = []

        for kw in keywords[:3]:
            try:
                results = await searxng_client.search(kw, limit=5)
                all_results.extend(results)
            except Exception as e:
                logger.warning(f"SearXNG search for '{kw}' failed: {e}")

        verification = Verification(
            buffer_item_id=item.id,
            search_keywords=keywords,
            search_engine="searxng",
            results=all_results[:10],
            status="completed",
            completed_at=datetime.utcnow(),
        )
        db.add(verification)

        try:
            prompt = f"标题：{entry.title}\n内容摘要：{entry.content[:500]}\n\n以下是搜索验证结果：\n"
            for r in all_results[:5]:
                prompt += f"- {r.get('title', '')}: {r.get('content', '')[:100]}\n"
            prompt += "\n请判断信息可信度，返回JSON: {\"confidence\": 0-100, \"verified\": bool, \"reason\": \"\"}"
            verdict = await llm_json(prompt, system="你是信息验证助手，只返回JSON。", max_tokens=300)

            confidence = verdict.get("confidence", 50)
            if verdict.get("verified", False):
                item.status = "verified"
                item.priority_score = max(item.priority_score, float(confidence))
            else:
                item.status = "rejected"
                item.priority_score = float(confidence) * 0.5
        except Exception as e:
            logger.error(f"LLM verification failed: {e}")
            item.status = "verified"
            item.priority_score = 50.0

        item.verification_count += 1
        await db.commit()

    await eng.dispose()
    return {"status": "ok", "item_id": buffer_item_id}


from app.celery_app import celery_app

@celery_app.task(name="app.tasks.verification.verify_item")
def verify_item(buffer_item_id: str):
    return asyncio.run(_verify_item(buffer_item_id))