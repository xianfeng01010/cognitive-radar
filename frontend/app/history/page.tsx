"use client";
import { useState, useEffect } from "react";
import { api } from "@/lib/api";

interface HistoryItem {
  id: string;
  type: string;
  keyword?: string;
  result_count?: number;
  strength?: string;
  content_type?: string;
  content_title?: string;
  url?: string;
  created_at: string | null;
}

export default function History() {
  const [items, setItems] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("all");

  const load = async () => {
    try {
      const data = await api.listHistory(filter, 50);
      setItems(data.history || []);
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  };

  useEffect(() => { load(); }, [filter]);

  const handleDelete = async (id: string) => {
    try { await api.deleteHistory(id); load(); }
    catch (e: any) { alert(e.message); }
  };

  const handleDeleteAll = async (type: string) => {
    const msg = type === "all" ? "确认删除全部历史？" : type === "search" ? "确认删除全部搜索历史？" : "确认删除全部浏览历史？";
    if (!confirm(msg)) return;
    try {
      if (type === "all") await api.deleteAllHistory();
      else if (type === "search") await api.deleteAllSearch();
      else await api.deleteAllView();
      load();
    } catch (e: any) { alert(e.message); }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">流量历史</h1>
          <p className="text-gray-500 text-sm mt-1">搜索历史 + 浏览历史</p>
        </div>
        <div className="flex gap-2">
          {["all", "search", "view"].map(t => (
            <button
              key={t}
              onClick={() => setFilter(t)}
              className={`px-3 py-1.5 rounded-lg text-sm ${filter === t ? "bg-blue-600 text-white" : "bg-white border border-gray-200 text-gray-600"}`}
            >
              {t === "all" ? "全部" : t === "search" ? "搜索" : "浏览"}
            </button>
          ))}
        </div>
      </div>

      <div className="flex gap-2">
        <button onClick={() => handleDeleteAll("search")} className="text-xs text-red-500 hover:text-red-700">清空搜索历史</button>
        <span className="text-gray-300">|</span>
        <button onClick={() => handleDeleteAll("view")} className="text-xs text-red-500 hover:text-red-700">清空浏览历史</button>
        <span className="text-gray-300">|</span>
        <button onClick={() => handleDeleteAll("all")} className="text-xs text-red-500 hover:text-red-700">清空全部</button>
      </div>

      {loading ? (
        <div className="text-gray-400 text-center py-12">加载中...</div>
      ) : items.length === 0 ? (
        <div className="bg-white rounded-lg border border-gray-200 p-12 text-center text-gray-400">
          暂无历史记录
        </div>
      ) : (
        <div className="bg-white rounded-lg border border-gray-200 divide-y divide-gray-100">
          {items.map((item, i) => (
            <div
              key={item.id}
              style={{ "--delay": `${i * 30}ms` } as React.CSSProperties}
              className="animate-fade-in-up flex items-center justify-between px-4 py-3 hover:bg-blue-50/30 transition-colors"
            >
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <span className={`text-xs px-2 py-0.5 rounded ${item.type === "search" ? "bg-blue-100 text-blue-700" : "bg-green-100 text-green-700"}`}>
                    {item.type === "search" ? "搜索" : "浏览"}
                  </span>
                  {item.strength && (
                    <span className="text-xs text-gray-400">{item.strength}</span>
                  )}
                  <span className="text-sm text-gray-900">
                    {item.keyword || item.content_title || "—"}
                  </span>
                  {item.result_count !== undefined && (
                    <span className="text-xs text-gray-400">({item.result_count}条结果)</span>
                  )}
                </div>
                {item.url && (
                  <a href={item.url} target="_blank" className="text-xs text-blue-500 hover:underline mt-1 block">
                    {item.url}
                  </a>
                )}
                {item.created_at && (
                  <span className="text-xs text-gray-400">{new Date(item.created_at).toLocaleString("zh-CN")}</span>
                )}
              </div>
              <button
                onClick={() => handleDelete(item.id)}
                className="text-red-400 hover:text-red-600 text-xs ml-4"
              >
                删除
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}