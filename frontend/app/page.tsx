"use client";
import { useState, useEffect } from "react";
import { api } from "@/lib/api";

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

const tierColors: Record<string, string> = {
  important: "bg-red-100 text-red-700",
  normal: "bg-blue-100 text-blue-700",
  low: "bg-gray-100 text-gray-600",
};

export default function Home() {
  const [pushes, setPushes] = useState<Push[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchKeyword, setSearchKeyword] = useState("");
  const [searching, setSearching] = useState(false);
  const [searchResult, setSearchResult] = useState<any>(null);

  const loadPushes = async () => {
    try {
      const data = await api.listPushes(20);
      setPushes(data.pushes || []);
    } catch (e) {
      console.error("Failed to load pushes", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadPushes(); }, []);

  const handleSearch = async () => {
    if (!searchKeyword.trim()) return;
    setSearching(true);
    setSearchResult(null);
    try {
      const result = await api.scan(searchKeyword);
      setSearchResult(result);
    } catch (e: any) {
      setSearchResult({ error: e.message });
    } finally {
      setSearching(false);
    }
  };

  const handleFeedback = async (pushId: string, feedback: "like" | "dislike") => {
    try {
      await api.pushFeedback(pushId, feedback);
      loadPushes();
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="space-y-6">
      {/* Search bar */}
      <div className="bg-white rounded-lg border border-gray-200 p-4">
        <div className="flex gap-2">
          <input
            type="text"
            value={searchKeyword}
            onChange={(e) => setSearchKeyword(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSearch()}
            placeholder="输入搜索关键词..."
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            onClick={handleSearch}
            disabled={searching}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            {searching ? "搜索中..." : "雷达搜索"}
          </button>
        </div>
      </div>

      {/* Search results */}
      {searchResult && (
        <div className="bg-white rounded-lg border border-gray-200 p-6 space-y-4">
          <div className="flex items-center gap-3">
            <h2 className="text-lg font-semibold">搜索结果</h2>
            <span className="text-xs px-2 py-1 rounded bg-gray-100 text-gray-600">
              强度: {searchResult.strength}
            </span>
            <span className="text-xs text-gray-400">共 {searchResult.total} 条</span>
          </div>

          {searchResult.clustered && (
            <div className="text-sm text-gray-500">
              <strong>聚类:</strong> {JSON.stringify(searchResult.clustered)}
            </div>
          )}

          {searchResult.report && (
            <div className="bg-blue-50 rounded-lg p-4 text-sm">
              <strong>报告:</strong> {JSON.stringify(searchResult.report)}
            </div>
          )}

          <div className="space-y-2">
            {searchResult.l1_results?.map((r: any, i: number) => (
              <div key={i} className="border-l-2 border-blue-400 pl-3">
                <a href={r.url} target="_blank" className="text-blue-600 hover:underline">{r.title}</a>
                <p className="text-sm text-gray-500">{r.content?.slice(0, 120)}</p>
              </div>
            ))}
            {searchResult.l2_results?.map((r: any, i: number) => (
              <div key={i} className="border-l-2 border-amber-400 pl-3">
                <a href={r.url} target="_blank" className="text-amber-600 hover:underline">{r.title}</a>
                <p className="text-sm text-gray-500">{r.outcome?.slice(0, 120)}</p>
              </div>
            ))}
            {searchResult.searxng_results?.map((r: any, i: number) => (
              <div key={i} className="border-l-2 border-gray-400 pl-3">
                <a href={r.url} target="_blank" className="text-gray-700 hover:underline">{r.title}</a>
                <p className="text-sm text-gray-500">{r.content?.slice(0, 120)}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Push list */}
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
    </div>
  );
}