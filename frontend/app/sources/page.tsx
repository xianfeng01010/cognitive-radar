"use client";
import { useState, useEffect } from "react";
import { api } from "@/lib/api";

interface Source {
  id: string;
  name: string;
  url: string;
  source_type: string;
  cache_level: string;
  trust_score: number;
  status: string;
  hit_count: number;
  last_hit_at: string | null;
  added_at: string | null;
}

export default function Sources() {
  const [sources, setSources] = useState<Source[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const [newUrl, setNewUrl] = useState("");
  const [newName, setNewName] = useState("");
  const [adding, setAdding] = useState(false);

  const load = async () => {
    try {
      const data = await api.listSources();
      setSources(data.sources || []);
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  };

  useEffect(() => { load(); }, []);

  const handleAdd = async () => {
    if (!newUrl.trim()) return;
    setAdding(true);
    try {
      await api.addSource({ url: newUrl, name: newName || undefined });
      setNewUrl(""); setNewName(""); setShowAdd(false);
      load();
    } catch (e: any) { alert(e.message); }
    finally { setAdding(false); }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("确认删除此来源？")) return;
    try { await api.deleteSource(id); load(); }
    catch (e: any) { alert(e.message); }
  };

  const l1Count = sources.filter(s => s.cache_level === "L1").length;
  const l2Count = sources.filter(s => s.cache_level === "L2").length;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">来源管理</h1>
          <p className="text-gray-500 text-sm mt-1">订阅源列表 + 信任分 + 缓存池状态</p>
        </div>
        <button
          onClick={() => setShowAdd(!showAdd)}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 active:scale-95 transition-all"
        >
          {showAdd ? "取消" : "+ 添加来源"}
        </button>
      </div>

      {showAdd && (
        <div className="bg-white rounded-lg border border-gray-200 p-4 space-y-3">
          <input
            type="text"
            value={newUrl}
            onChange={(e) => setNewUrl(e.target.value)}
            placeholder="RSS Feed URL"
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <input
            type="text"
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            placeholder="名称（可选）"
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            onClick={handleAdd}
            disabled={adding}
            className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
          >
            {adding ? "添加中..." : "确认添加"}
          </button>
        </div>
      )}

      <div className="grid grid-cols-2 gap-4">
        <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg border border-blue-200 p-6">
          <h2 className="font-semibold text-lg mb-2 text-blue-900">L1 核心订阅</h2>
          <p className="text-3xl font-bold text-blue-600">{l1Count}</p>
          <p className="text-blue-400 text-sm mt-1">预设 / 晋升的高质量源</p>
        </div>
        <div className="bg-gradient-to-br from-amber-50 to-amber-100 rounded-lg border border-amber-200 p-6">
          <h2 className="font-semibold text-lg mb-2 text-amber-900">L2 候选订阅</h2>
          <p className="text-3xl font-bold text-amber-600">{l2Count}</p>
          <p className="text-amber-400 text-sm mt-1">拓展搜索发现的候选源</p>
        </div>
      </div>

      {loading ? (
        <div className="text-gray-400 text-center py-12">加载中...</div>
      ) : sources.length === 0 ? (
        <div className="bg-white rounded-lg border border-gray-200 p-12 text-center text-gray-400">
          暂无订阅源，点击「添加来源」开始
        </div>
      ) : (
        <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="text-left px-4 py-3 font-medium text-gray-600">名称</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">级别</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">信任分</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">命中</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">状态</th>
                <th className="text-right px-4 py-3 font-medium text-gray-600">操作</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {sources.map((s) => (
                <tr key={s.id} className="hover:bg-blue-50/30 transition-colors">
                  <td className="px-4 py-3">
                    <div className="font-medium text-gray-900">{s.name}</div>
                    <div className="text-xs text-gray-400 truncate max-w-xs">{s.url}</div>
                  </td>
                  <td className="px-4 py-3">
                    <span className={s.cache_level === "L1" ? "text-blue-600 font-medium" : "text-amber-600"}>
                      {s.cache_level}
                    </span>
                  </td>
                  <td className="px-4 py-3">{s.trust_score.toFixed(1)}</td>
                  <td className="px-4 py-3">{s.hit_count}</td>
                  <td className="px-4 py-3">
                    <span className={`text-xs px-2 py-0.5 rounded ${
                      s.status === "active" ? "bg-green-100 text-green-700" :
                      s.status === "expired" ? "bg-red-100 text-red-700" :
                      "bg-gray-100 text-gray-600"
                    }`}>{s.status}</span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <button
                      onClick={() => handleDelete(s.id)}
                      className="text-red-500 hover:text-red-700 text-xs"
                    >
                      删除
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}