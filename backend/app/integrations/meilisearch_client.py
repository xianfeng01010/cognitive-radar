import meilisearch
from app.config import settings

meili_client = meilisearch.Client(settings.MEILI_URL, settings.MEILI_KEY)

INDEX_ENTRIES = "entries"
INDEX_CASES = "cases"
INDEX_PROVENANCE = "provenance_trees"


async def init_indexes():
    for index_uid, primary_key in [
        (INDEX_ENTRIES, "id"),
        (INDEX_CASES, "id"),
        (INDEX_PROVENANCE, "id"),
    ]:
        try:
            meili_client.get_index(index_uid)
        except Exception:
            meili_client.create_index(index_uid, {"primaryKey": primary_key})

    entries_index = meili_client.index(INDEX_ENTRIES)
    entries_index.update_searchable_attributes(["title", "content", "keywords"])
    entries_index.update_filterable_attributes(["source_type", "source_id", "published_at"])
    entries_index.update_sortable_attributes(["published_at", "collected_at"])

    cases_index = meili_client.index(INDEX_CASES)
    cases_index.update_searchable_attributes(["title", "who", "outcome", "keywords"])
    cases_index.update_filterable_attributes(["verification_status", "trust_score"])


async def add_documents(index_uid: str, documents: list[dict]):
    meili_client.index(index_uid).add_documents(documents)


async def search_entries(query: str, limit: int = 20, filters: str = "") -> list[dict]:
    opts = {"limit": limit}
    if filters:
        opts["filter"] = filters
    results = meili_client.index(INDEX_ENTRIES).search(query, opts)
    return results.get("hits", [])


async def search_cases(query: str, limit: int = 10) -> list[dict]:
    results = meili_client.index(INDEX_CASES).search(query, {"limit": limit})
    return results.get("hits", [])