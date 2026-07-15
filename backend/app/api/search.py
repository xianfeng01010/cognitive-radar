from fastapi import APIRouter

router = APIRouter()


@router.post("/scan")
async def scan(keyword: str):
    return {
        "status": "not_implemented",
        "keyword": keyword,
        "message": "搜索功能开发中",
    }


@router.get("/strength")
async def classify_strength(keyword: str):
    import re
    strong_patterns = [
        r"如何|怎么|怎样|方法|经验|教程|指南",
        r"how to|guide|tutorial|experience|method",
        r"选择.*还是|应该.*吗|值不值得",
    ]
    if any(re.search(p, keyword) for p in strong_patterns):
        strength = "strong"
    elif any(re.search(p, keyword) for p in [r"哪里|什么好吃|好玩|天气|怎么样", r"今天|明天|本周|周末"]):
        strength = "weak"
    else:
        strength = "medium"
    return {"keyword": keyword, "strength": strength}