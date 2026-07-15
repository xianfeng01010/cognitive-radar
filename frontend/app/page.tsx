"use client";
import { useState, useEffect, useCallback } from "react";
import { api } from "@/lib/api";

interface CardItem {
  id: string;
  title: string;
  content_preview: string;
  source: string;
  url: string;
  cache_level: string;
  trust_score: number;
  published_date: string;
  thumbnail: string;
  engines: string[];
}

interface ScanResultData {
  strength: string;
  total: number;
  keyword: string;
  page: number;
  page_size: number;
  total_pages: number;
}

interface CardDetail {
  title: string;
  tldr: string;
  key_findings: string[];
  key_entities: string[];
  timeline: string[];
  conclusion: string;
  source_url: string;
}

interface Push {
  id: string;
  push_tier: string;
  content_snapshot: {
    title: string;
    url: string;
    content_preview: string;
    source_name: string;
    priority_score: number;
  };
  trust_score_at_push: number;
  user_feedback: string | null;
  created_at: string | null;
}

const cacheColors: Record<string, string> = {
  L1: "bg-blue-100 text-blue-700 border-blue-200",
  L2: "bg-amber-100 text-amber-700 border-amber-200",
  SearXNG: "bg-gray-100 text-gray-600 border-gray-200",
};

const tierColors: Record<string, string> = {
  important: "bg-red-100 text-red-700",
  normal: "bg-blue-100 text-blue-700",
  low: "bg-gray-100 text-gray-600",
};

const PAGE_SIZE = 12;

export default function Home() {
  const [pushes, setPushes] = useState<Push[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchKeyword, setSearchKeyword] = useState("");
  const [searching, setSearching] = useState(false);
  const [cards, setCards] = useState<CardItem[]>([]);
  const [searchMeta, setSearchMeta] = useState<ScanResultData | null>(null);
  const [currentPage, setCurrentPage] = useState(1);

  const [selectedCard, setSelectedCard] = useState<CardItem | null>(null);
  const [detail, setDetail] = useState<CardDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);

  const loadPushes = useCallback(async () => {
    try {
      const data = await api.listPushes(20);
      setPushes(data.pushes || []);
    } catch (e) {
      console.error("Failed to load pushes", e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadPushes(); }, [loadPushes]);

  const handleSearch = async (page: number = 1) => {
    if (!searchKeyword.trim()) return;
    setSearching(true);
    setCards([]);
    setSearchMeta(null);
    setCurrentPage(page);
    try {
      const result = await api.scan(searchKeyword, false, page, PAGE_SIZE);
      setCards(result.cards || []);
      setSearchMeta({
        strength: result.strength,
        total: result.total,
        keyword: result.keyword,
        page: result.page,
        page_size: result.page_size,
        total_pages: result.total_pages,
      });
    } catch (e: any) {
      setSearchMeta({ strength: "error", total: 0, keyword: searchKeyword, page: 1, page_size: PAGE_SIZE, total_pages: 1 });
      console.error(e);
    } finally {
      setSearching(false);
    }
  };

  const handlePageChange = (page: number) => {
    handleSearch(page);
  };

  const handleCardClick = async (card: CardItem) => {
    setSelectedCard(card);
    setDetail(null);
    setDetailLoading(true);
    try {
      const result = await api.getCardDetail({
        title: card.title,
        content: card.content_preview,
        url: card.url,
        source: card.source,
      });
      setDetail(result);
    } catch (e) {
      console.error(e);
      setDetail({
        title: card.title,
        tldr: "详情获取失败",
        key_findings: [],
        key_entities: [],
        timeline: [],
        conclusion: "",
        source_url: card.url,
      });
    } finally {
      setDetailLoading(false);
    }
  };

  const closeModal = () => {
    setSelectedCard(null);
    setDetail(null);
    setDetailLoading(false);
  };

  const handleFeedback = async (pushId: string, feedback: "like" | "dislike") => {
    try {
      await api.pushFeedback(pushId, feedback);
      loadPushes();
    } catch (e) { console.error(e); }
  };

  // Build page number list for pagination
  const getPageNumbers = (): number[] => {
    if (!searchMeta) return [];
    const { page, total_pages } = searchMeta;
    const nums: number[] = [];
    const start = Math.max(1, page - 2);
    const end = Math.min(total_pages, page + 2);
    for (let i = start; i <= end; i++) nums.push(i);
    return nums;
  };

  return (
    <div className="space-y-6">
      {/* Search bar */}
      <div className="bg-white rounded-lg border border-gray-200 p-4 sticky top-0 z-10 shadow-sm">
        <div className="flex gap-2">
          <input
            type="text"
            value={searchKeyword}
            onChange={(e) => setSearchKeyword(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSearch(1)}
            placeholder="输入搜索关键词..."
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            onClick={() => handleSearch(1)}
            disabled={searching}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            {searching ? "搜索中..." : "雷达搜索"}
          </button>
        </div>
      </div>

      {/* Search results — Masonry waterfall */}
      {searchMeta && (
        <div className="flex items-center gap-3">
          <h2 className="text-lg font-semibold text-gray-900">搜索结果</h2>
          <span className="text-xs px-2 py-1 rounded bg-gray-100 text-gray-600">
            强度: {searchMeta.strength}
          </span>
          <span className="text-xs text-gray-400">共 {searchMeta.total} 条</span>
          <span className="text-xs text-gray-400">第 {searchMeta.page}/{searchMeta.total_pages} 页</span>
        </div>
      )}

      {cards.length > 0 && (
        <div className="columns-1 md:columns-2 lg:columns-3 gap-4 [column-fill:_balance]">
          {cards.map((card, i) => (
            <div
              key={i}
              onClick={() => handleCardClick(card)}
              className="mb-4 break-inside-avoid bg-white rounded-lg border border-gray-200 overflow-hidden cursor-pointer hover:shadow-md hover:border-blue-300 transition-all"
            >
              {/* Thumbnail */}
              {card.thumbnail && (
                <img
                  src={card.thumbnail}
                  alt=""
                  className="w-full h-40 object-cover"
                  onError={(e) => { (e.target as HTMLImageElement).style.display = 'none'; }}
                />
              )}

              <div className="p-5">
                {/* Badges */}
                <div className="flex flex-wrap items-center gap-1.5 mb-2">
                  <span className={`text-xs px-2 py-0.5 rounded border ${cacheColors[card.cache_level] || cacheColors.SearXNG}`}>
                    {card.cache_level}
                  </span>
                  {card.engines.length > 0 && card.engines.map((eng, j) => (
                    <span key={j} className="text-xs px-1.5 py-0.5 rounded bg-gray-50 text-gray-500 border border-gray-100">
                      {eng}
                    </span>
                  ))}
                  {card.trust_score > 0 && (
                    <span className="text-xs text-gray-400 ml-auto">信任 {card.trust_score.toFixed(0)}</span>
                  )}
                </div>

                {/* Title */}
                <h3 className="font-medium text-gray-900 mb-2 leading-snug">{card.title}</h3>

                {/* Content preview — detailed */}
                {card.content_preview && (
                  <p className="text-sm text-gray-500 leading-relaxed line-clamp-8 mb-2">{card.content_preview}</p>
                )}

                {/* Footer */}
                <div className="flex items-center gap-3 pt-2 border-t border-gray-50">
                  {card.source && (
                    <span className="text-xs text-gray-400 truncate">来源: {card.source}</span>
                  )}
                  {card.published_date && (
                    <span className="text-xs text-gray-400 ml-auto">{card.published_date}</span>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Pagination */}
      {searchMeta && searchMeta.total_pages > 1 && (
        <div className="flex items-center justify-center gap-2 py-4">
          <button
            onClick={() => handlePageChange(currentPage - 1)}
            disabled={currentPage <= 1 || searching}
            className="px-3 py-1.5 text-sm border border-gray-200 rounded-lg hover:bg-gray-50 disabled:opacity-30"
          >
            上一页
          </button>
          {getPageNumbers().map((num) => (
            <button
              key={num}
              onClick={() => handlePageChange(num)}
              disabled={searching}
              className={`px-3 py-1.5 text-sm rounded-lg ${
                num === currentPage
                  ? "bg-blue-600 text-white"
                  : "border border-gray-200 hover:bg-gray-50"
              }`}
            >
              {num}
            </button>
          ))}
          <button
            onClick={() => handlePageChange(currentPage + 1)}
            disabled={currentPage >= searchMeta.total_pages || searching}
            className="px-3 py-1.5 text-sm border border-gray-200 rounded-lg hover:bg-gray-50 disabled:opacity-30"
          >
            下一页
          </button>
        </div>
      )}

      {/* Push list */}
      {cards.length === 0 && (
        <div>
          <h1 className="text-2xl font-bold text-gray-900 mb-4">最近推送</h1>
          {loading ? (
            <div className="text-gray-400 text-center py-12">加载中...</div>
          ) : pushes.length === 0 ? (
            <div className="bg-white rounded-lg border border-gray-200 p-12 text-center text-gray-400">
              暂无推送内容，系统正在运行中...
            </div>
          ) : (
            <div className="space-y-3">
              {pushes.map((push) => (
                <div key={push.id} className="bg-white rounded-lg border border-gray-200 p-5">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <span className={`text-xs px-2 py-0.5 rounded ${tierColors[push.push_tier] || tierColors.low}`}>
                          {push.push_tier}
                        </span>
                        <span className="text-xs text-gray-400">
                          信任分: {push.trust_score_at_push.toFixed(1)}
                        </span>
                        {push.created_at && (
                          <span className="text-xs text-gray-400">
                            {new Date(push.created_at).toLocaleString("zh-CN")}
                          </span>
                        )}
                      </div>
                      <a
                        href={push.content_snapshot.url}
                        target="_blank"
                        className="text-lg font-medium text-gray-900 hover:text-blue-600"
                      >
                        {push.content_snapshot.title}
                      </a>
                      {push.content_snapshot.source_name && (
                        <p className="text-xs text-gray-400 mt-1">来源: {push.content_snapshot.source_name}</p>
                      )}
                    </div>
                    <div className="flex gap-1">
                      <button
                        onClick={() => handleFeedback(push.id, "like")}
                        className={`px-3 py-1 rounded text-sm ${push.user_feedback === "like" ? "bg-green-100 text-green-700" : "text-gray-400 hover:bg-gray-100"}`}
                      >
                        👍
                      </button>
                      <button
                        onClick={() => handleFeedback(push.id, "dislike")}
                        className={`px-3 py-1 rounded text-sm ${push.user_feedback === "dislike" ? "bg-red-100 text-red-700" : "text-gray-400 hover:bg-gray-100"}`}
                      >
                        👎
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Detail Modal — Fixed Template */}
      {selectedCard && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50" onClick={closeModal}>
          <div
            className="bg-white rounded-xl max-w-2xl w-full max-h-[85vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            {detailLoading ? (
              <div className="p-12 text-center text-gray-400">
                <div className="animate-spin inline-block w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full mb-3" />
                <p>正在生成结构化摘要...</p>
              </div>
            ) : detail ? (
              <div className="p-6 space-y-5">
                {/* Header */}
                <div className="flex items-start justify-between gap-4 border-b border-gray-100 pb-4">
                  <h2 className="text-xl font-bold text-gray-900 leading-snug">{detail.title}</h2>
                  <button onClick={closeModal} className="text-gray-400 hover:text-gray-600 text-2xl leading-none flex-shrink-0">&times;</button>
                </div>

                {/* TL;DR */}
                {detail.tldr && (
                  <div className="bg-blue-50 rounded-lg p-4">
                    <div className="text-xs font-semibold text-blue-600 mb-1">一句话摘要</div>
                    <p className="text-sm text-gray-700">{detail.tldr}</p>
                  </div>
                )}

                {/* Key Findings */}
                {detail.key_findings.length > 0 && (
                  <div>
                    <div className="text-xs font-semibold text-gray-500 mb-2">关键发现</div>
                    <ul className="space-y-1.5">
                      {detail.key_findings.map((f, i) => (
                        <li key={i} className="text-sm text-gray-700 flex gap-2">
                          <span className="text-blue-500 flex-shrink-0">{i + 1}.</span>
                          <span>{f}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Key Entities */}
                {detail.key_entities.length > 0 && (
                  <div>
                    <div className="text-xs font-semibold text-gray-500 mb-2">关键人物 / 机构</div>
                    <div className="flex flex-wrap gap-2">
                      {detail.key_entities.map((e, i) => (
                        <span key={i} className="text-xs px-2 py-1 rounded-full bg-purple-100 text-purple-700">{e}</span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Timeline */}
                {detail.timeline.length > 0 && (
                  <div>
                    <div className="text-xs font-semibold text-gray-500 mb-2">时间线</div>
                    <div className="space-y-1.5 border-l-2 border-gray-200 pl-3">
                      {detail.timeline.map((t, i) => (
                        <div key={i} className="text-sm text-gray-700 relative">
                          <span className="absolute -left-[17px] top-1.5 w-2 h-2 rounded-full bg-gray-400" />
                          {t}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Conclusion */}
                {detail.conclusion && (
                  <div>
                    <div className="text-xs font-semibold text-gray-500 mb-2">结论</div>
                    <p className="text-sm text-gray-700 leading-relaxed">{detail.conclusion}</p>
                  </div>
                )}

                {/* Source */}
                {detail.source_url && (
                  <div className="border-t border-gray-100 pt-4 flex items-center gap-3">
                    <a
                      href={detail.source_url}
                      target="_blank"
                      className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700"
                    >
                      查看原文
                    </a>
                    <span className="text-xs text-gray-400 truncate">{detail.source_url}</span>
                  </div>
                )}
              </div>
            ) : null}
          </div>
        </div>
      )}
    </div>
  );
}