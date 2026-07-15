# 认知雷达 (Cognitive Radar)

> Search-driven self-growing information network. 搜索驱动的自生长信息网络.

你搜索 → 系统从订阅中找答案 → 不够就拓展 → 发现新源建议订阅 → 订阅增长 → 低质源自动清理 → 信噪比持续优化.

## Tech Stack

| 层 | 组件 | 选型 |
|---|------|------|
| RSS | 阅读器 | Miniflux (预留抽象层，可切换 FreshRSS) |
| RSS | 生成器 | RSSHub (后期启用) |
| 数据库 | 主库 | PostgreSQL 16 + pgvector |
| 搜索 | 全文 | Meilisearch v1.37 |
| 搜索 | 外部 | SearXNG |
| 后端 | 框架 | FastAPI |
| 任务 | 队列 | Celery + Redis |
| 前端 | Web看板 | Next.js 14 + Tailwind |
| AI | LLM | opencode-go (deepseek-v4-flash-free) |
| 部署 | 方式 | Docker Compose |
| 代理 | 反向 | Caddy |

## Quick Start

```bash
# 1. Clone
git clone https://github.com/xianfeng01010/cognitive-radar.git
cd cognitive-radar

# 2. Copy env
cp .env.example .env

# 3. Start all services
docker compose up -d

# 4. Verify
curl http://localhost:8000/          # API
curl http://localhost:8000/docs        # Swagger
open http://localhost:3000            # Web 看板
open http://localhost:8080            # Miniflux
open http://localhost:7700            # Meilisearch
```

## Services

| 服务 | 端口 | 说明 |
|------|------|------|
| API (FastAPI) | 8000 | 后端 API + Swagger |
| Web (Next.js) | 3000 | Web 看板 |
| PostgreSQL | 5432 | 主数据库 + pgvector |
| Redis | 6379 | 缓存 + Celery Broker |
| Meilisearch | 7700 | 全文搜索 |
| Miniflux | 8080 | RSS 采集 |
| SearXNG | 8888 | 外部搜索 |
| Caddy | 80 | 反向代理 |

## Project Structure

```
cognitive-radar/
├── docker-compose.yml
├── .env.example
├── Caddyfile
├── searxng/
│   └── settings.yml
├── backend/                    # FastAPI
│   ├── Dockerfile
│   ├── pyproject.toml
│   └── app/
│       ├── main.py
│       ├── config.py
│       ├── celery_app.py
│       ├── models/            # SQLAlchemy
│       ├── api/               # Routes
│       ├── services/          # Business logic
│       ├── integrations/      # External services
│       │   ├── opencode.py    # LLM
│       │   ├── meilisearch_client.py
│       │   ├── searxng_client.py
│       │   └── rss/            # RSS engine abstraction
│       └── tasks/             # Celery tasks
└── frontend/                  # Next.js
    ├── Dockerfile
    ├── package.json
    └── app/
        ├── layout.tsx
        ├── page.tsx           # 最近推送
        ├── sources/           # 来源管理
        ├── health/            # 系统健康
        └── history/           # 流量历史
```

## Design Principles

- **真实 > 正确性 > 覆盖率 > 及时性**
- 反幻觉 · 自我校准 · 透明可审计

## License

MIT