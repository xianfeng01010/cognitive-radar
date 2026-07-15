"use client";
import { useState, useEffect, useCallback, useRef } from "react";
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

interface HistoryItem {
  id: string;
  keyword: string;
  result_count: number;
  strength: string;
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
  const [searchHistory, setSearchHistory] = useState<HistoryItem[]>([]);

  const [selectedCard, setSelectedCard] = useState<CardItem | null>(null);
  const [detail, setDetail] = useState<CardDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const detailReqId = useRef(0);

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

  const loadHistory = useCallback(async () => {
    try {
      const data = await api.searchHistory(8);
      setSearchHistory(data.history || []);
    } catch (e) {
      console.error("Failed to load search history", e);
    }
  }, []);

  useEffect(() => {
    loadPushes();
    loadHistory();
  }, [loadPushes, loadHistory]);

  // Lock body scroll when modal is open
  useEffect(() => {
    if (selectedCard) {
      document.body.classList.add("modal-open");
    } else {
      document.body.classList.remove("modal-open");
    }
    return () => document.body.classList.remove("modal-open");
  }, [selectedCard]);

  // Escape key to close modal
  useEffect(() => {
    if (!selectedCard) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") closeModal();
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [selectedCard]);

  const handleSearch = async (keyword: string, page: number = 1) => {
    const kw = keyword || searchKeyword;
    if (!kw.trim()) {
      // F2: Clear search when empty keyword submitted
      setCards([]);
      setSearchMeta(null);
      setCurrentPage(1);
      return;
    }
    setSearchKeyword(kw);
    setSearching(true);
    setCards([]);
    setSearchMeta(null);
    setCurrentPage(page);
    try {
      const result = await api.scan(kw, false, page, PAGE_SIZE);
      setCards(result.cards || []);
      setSearchMeta({
        strength: result.strength,
        total: result.total,
        keyword: result.keyword,
        page: result.page,
        page_size: result.page_size,
        total_pages: result.total_pages,
      });
      // F4: Refresh search history after successful search
      loadHistory();
    } catch (e: any) {
      setSearchMeta({ strength: "error", total: 0, keyword: kw, page: 1, page_size: PAGE_SIZE, total_pages: 1 });
      console.error(e);
    } finally {
      setSearching(false);
    }
  };

  const handleClearSearch = () => {
    setSearchKeyword("");
    setCards([]);
    setSearchMeta(null);
    setCurrentPage(1);
  };

  const handlePageChange = (page: number) => {
    handleSearch(searchKeyword, page);
  };

  const handleHistoryClick = (kw: string) => {
    handleSearch(kw, 1);
  };

  // F1: Race condition fix - request ID guard
  const handleCardClick = async (card: CardItem) => {
    setSelectedCard(card);
    setDetail(null);
    setDetailLoading(true);
    const reqId = ++detailReqId.current;
    try {
      const result = await api.getCardDetail({
        title: card.title,
        content: card.content_preview,
        url: card.url,
        source: card.source,
      });
      if (reqId !== detailReqId.current) return;
      setDetail(result);
    } catch (e) {
      if (reqId !== detailReqId.current) return;
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
      if (reqId === detailReqId.current) setDetailLoading(false);
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

  const getPageNumbers = (): number[] => {
    if (!searchMeta) return [];
    const { page, total_pages } = searchMeta;
    const nums: number[] = [];
    const start = Math.max(1, page - 2);
    const end = Math.min(total_pages, page + 2);
    for (let i = start; i <= end; i++) nums.push(i);
    return nums;
  };

  // F3: Fix hasSearch - based on searchMeta, not cards.length
  const hasSearch = searchMeta !== null || searching;

  return (
    <div className="space-y-6">
      {/* ── Search Section (sticky) ── */}
      <div className="sticky top-[57px] z-30 -mx-6 px-6 py-3 bg-white/80 backdrop-blur-md border-b border-gray-200/60">
        <div className="flex gap-2">
          <input
            type="text"
            value={searchKeyword}
            onChange={(e) => setSearchKeyword(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSearch(searchKeyword, 1)}
            placeholder="输入搜索关键词..."
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
          />
          {searchMeta && (
            <button
              onClick={handleClearSearch}
              className="px-3 py-2 text-gray-400 hover:text-gray-600 text-sm border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
              title="清除搜索"
            >
              ✕
            </button>
          )}
          <button
            onClick={() => handleSearch(searchKeyword, 1)}
            disabled={searching}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors active:scale-95"
          >
            {searching ? "搜索中..." : "雷达搜索"}
          </button>
        </div>

        {/* Search history chips - only when no active search */}
        {!hasSearch && searchHistory.length > 0 && (
          <div className="flex items-center gap-2 mt-2 flex-wrap">
            <span className="text-xs text-gray-400">最近搜索:</span>
            {searchHistory.map((h) => (
              <button
                key={h.id}
                onClick={() => handleHistoryClick(h.keyword)}
                className="text-xs px-2.5 py-1 rounded-full bg-gray-100 hover:bg-blue-50 hover:text-blue-600 text-gray-600 transition-colors"
              >
                {h.keyword}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* ── Summary Panel (only after search) ── */}
      {searchMeta && (
        <div className="animate-fade-in-up bg-white rounded-xl border border-gray-200 p-4 shadow-sm">
          <div className="flex items-center gap-3 flex-wrap">
            <span className="text-lg font-semibold text-gray-900">"{searchMeta.keyword}"</span>
            <span className="text-xs px-2 py-0.5 rounded bg-gray-100 text-gray-600">
              强度: {searchMeta.strength}
            </span>
            <span className="text-sm text-gray-400">共 {searchMeta.total} 条</span>
            <span className="text-sm text-gray-400 ml-auto">第 {searchMeta.page}/{searchMeta.total_pages} 页</span>
          </div>
        </div>
      )}

      {/* ── Searching skeleton ── */}
      {searching && (
        <div className="columns-1 md:columns-2 lg:columns-3 gap-4">
          {[1,2,3,4,5,6].map((i) => (
            <div key={i} className="mb-4 break-inside-avoid bg-white rounded-lg border border-gray-200 p-5">
              <div className="h-4 bg-gray-100 rounded w-1/3 mb-3 animate-pulse" />
              <div className="h-5 bg-gray-100 rounded w-3/4 mb-2 animate-pulse" />
              <div className="h-3 bg-gray-100 rounded w-full mb-1 animate-pulse" />
              <div className="h-3 bg-gray-100 rounded w-5/6 animate-pulse" />
            </div>
          ))}
        </div>
      )}

      {/* ── Masonry Waterfall ── */}
      {cards.length > 0 && (
        <div className="columns-1 md:columns-2 lg:columns-3 gap-4 [column-fill:_balance]">
          {cards.map((card, i) => (
            <div
              key={card.id || i}
              onClick={() => handleCardClick(card)}
              style={{ "--delay": `${i * 50}ms` } as React.CSSProperties}
              className="animate-fade-in-up mb-4 break-inside-avoid bg-white rounded-lg border border-gray-200 overflow-hidden cursor-pointer hover:shadow-lg hover:border-blue-300 hover:-translate-y-0.5 transition-all duration-200"
            >
              {card.thumbnail && (
                <img
                  src={card.thumbnail}
                  alt=""
                  className="w-full h-40 object-cover"
                  onError={(e) => { (e.target as HTMLImageElement).style.display = 'none'; }}
                />
              )}
              <div className="p-5">
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
                <h3 className="font-medium text-gray-900 mb-2 leading-snug">{card.title}</h3>
                {card.content_preview && (
                  <p className="text-sm text-gray-500 leading-relaxed line-clamp-8 mb-2">{card.content_preview}</p>
                )}
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

      {/* ── Pagination ── */}
      {searchMeta && searchMeta.total_pages > 1 && (
        <div className="flex items-center justify-center gap-2 py-4">
          <button
            onClick={() => handlePageChange(currentPage - 1)}
            disabled={currentPage <= 1 || searching}
            className="px-3 py-1.5 text-sm border border-gray-200 rounded-lg hover:bg-gray-50 disabled:opacity-30 transition-colors active:scale-95"
          >
            上一页
          </button>
          {getPageNumbers().map((num) => (
            <button
              key={num}
              onClick={() => handlePageChange(num)}
              disabled={searching}
              className={`px-3 py-1.5 text-sm rounded-lg transition-all active:scale-95 ${
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
            className="px-3 py-1.5 text-sm border border-gray-200 rounded-lg hover:bg-gray-50 disabled:opacity-30 transition-colors active:scale-95"
          >
            下一页
          </button>
        </div>
      )}

      {/* ── Push list (only when no search) ── */}
      {!hasSearch && (
        <div>
          <h1 className="text-2xl font-bold text-gray-900 mb-4">最近推送</h1>
          {loading ? (
            <div className="text-gray-400 text-center py-12">加载中...</div>
          ) : pushes.length === 0 ? (
            <div className="bg-white rounded-lg border border-gray-200 p-12 text-center text-gray-400">
              暂无推送内容，系统正在运行中...
            </div>
          ) : (
            <div className="space-y-3 max-w-3xl mx-auto">
              {pushes.map((push, i) => (
                <div
                  key={push.id}
                  style={{ "--delay": `${i * 50}ms` } as React.CSSProperties}
                  className="animate-fade-in-up bg-white rounded-lg border border-gray-200 p-5 hover:shadow-md transition-shadow"
                >
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
                        className="text-lg font-medium text-gray-900 hover:text-blue-600 transition-colors"
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
                        className={`px-3 py-1 rounded text-sm transition-colors ${push.user_feedback === "like" ? "bg-green-100 text-green-700" : "text-gray-400 hover:bg-gray-100"}`}
                      >
                        👍
                      </button>
                      <button
                        onClick={() => handleFeedback(push.id, "dislike")}
                        className={`px-3 py-1 rounded text-sm transition-colors ${push.user_feedback === "dislike" ? "bg-red-100 text-red-700" : "text-gray-400 hover:bg-gray-100"}`}
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

      {/* ── Detail Modal - Fixed Template + Scroll Isolation ── */}
      {selectedCard && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 animate-fade-in touch-none"
          onClick={closeModal}
        >
          <div
            className="animate-scale-in bg-white rounded-xl max-w-2xl w-full max-h-[85vh] overflow-y-auto overscroll-contain shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            {detailLoading ? (
              <div className="p-12 text-center text-gray-400">
                <div className="animate-spin inline-block w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full mb-3" />
                <p>正在生成结构化摘要...</p>
              </div>
            ) : detail ? (
              <div className="p-6 space-y-5">
                <div className="flex items-start justify-between gap-4 border-b border-gray-100 pb-4">
                  <h2 className="text-xl font-bold text-gray-900 leading-snug">{detail.title}</h2>
                  <button
                    onClick={closeModal}
                    className="text-gray-400 hover:text-gray-600 text-2xl leading-none flex-shrink-0 transition-colors"
                  >
                    &times;
                  </button>
                </div>

                {detail.tldr && (
                  <div className="bg-blue-50 rounded-lg p-4">
                    <div className="text-xs font-semibold text-blue-600 mb-1">一句话摘要</div>
                    <p className="text-sm text-gray-700">{detail.tldr}</p>
                  </div>
                )}

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

                {detail.conclusion && (
                  <div>
                    <div className="text-xs font-semibold text-gray-500 mb-2">结论</div>
                    <p className="text-sm text-gray-700 leading-relaxed">{detail.conclusion}</p>
                  </div>
                )}

                {detail.source_url && (
                  <div className="border-t border-gray-100 pt-4 flex items-center gap-3">
                    <a
                      href={detail.source_url}
                      target="_blank"
                      className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700 transition-colors active:scale-95"
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