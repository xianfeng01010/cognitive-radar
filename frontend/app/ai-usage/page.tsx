"use client";
import { useState, useEffect } from "react";
import { api } from "@/lib/api";

interface UsageItem {
  id: string;
  provider: string;
  model: string;
  task_type: string;
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  latency_ms: number;
  success: boolean;
  error: string | null;
  created_at: string | null;
}

interface Stats {
  total_calls: number;
  total_tokens: number;
  by_provider: { provider: string; calls: number; tokens: number }[];
  by_task: { task_type: string; calls: number; tokens: number }[];
}

const taskLabels: Record<string, string> = {
  cluster: "聚类",
  report: "报告",
  health_check: "健康检查",
  verify: "验证",
  unknown: "其他",
};

export default function AIUsagePage() {
  const [items, setItems] = useState<UsageItem[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  const [filterProvider, setFilterProvider] = useState("");
  const [filterTask, setFilterTask] = useState("");
  const [offset, setOffset] = useState(0);
  const [total, setTotal] = useState(0);
  const limit = 50;

  const load = async () => {
    setLoading(true);
    try {
      const params: any = { limit, offset };
      if (filterProvider) params.provider = filterProvider;
      if (filterTask) params.task_type = filterTask;
      const [usageData, statsData] = await Promise.all([
        api.listAIUsage(params),
        api.aiUsageStats(),
      ]);
      setItems(usageData.items || []);
      setTotal(usageData.total || 0);
      setStats(statsData);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, [filterProvider, filterTask, offset]);

  const providerColor = (p: string) => {
    if (p === "opencode") return "bg-blue-100 text-blue-700";
    if (p === "volcengine") return "bg-orange-100 text-orange-700";
    return "bg-gray-100 text-gray-700";
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">AI 用量</h1>
        <p className="text-gray-500 text-sm mt-1">LLM 调用记录与 Token 消耗统计</p>
      </div>

      {stats && (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="bg-white rounded-lg border border-gray-200 p-4">
            <div className="text-xs text-gray-400 mb-1">总调用次数</div>
            <div className="text-2xl font-bold text-gray-900">{stats.total_calls}</div>
          </div>
          <div className="bg-white rounded-lg border border-gray-200 p-4">
            <div className="text-xs text-gray-400 mb-1">总 Token 消耗</div>
            <div className="text-2xl font-bold text-gray-900">{stats.total_tokens.toLocaleString()}</div>
          </div>
          <div className="bg-white rounded-lg border border-gray-200 p-4">
            <div className="text-xs text-gray-400 mb-1">Provider 分布</div>
            <div className="flex flex-col gap-1">
              {stats.by_provider.map((p) => (
                <div key={p.provider} className="flex items-center justify-between text-sm">
                  <span className={`px-2 py-0.5 rounded text-xs ${providerColor(p.provider)}`}>{p.provider}</span>
                  <span className="text-gray-500">{p.calls} 次 / {p.tokens.toLocaleString()} tok</span>
                </div>
              ))}
              {stats.by_provider.length === 0 && <span className="text-gray-300 text-sm">暂无数据</span>}
            </div>
          </div>
        </div>
      )}

      <div className="flex items-center gap-2 flex-wrap">
        <select
          value={filterProvider}
          onChange={(e) => { setFilterProvider(e.target.value); setOffset(0); }}
          className="text-sm border border-gray-200 rounded-lg px-3 py-1.5 bg-white"
        >
          <option value="">全部 Provider</option>
          <option value="opencode">opencode</option>
          <option value="volcengine">volcengine</option>
        </select>
        <select
          value={filterTask}
          onChange={(e) => { setFilterTask(e.target.value); setOffset(0); }}
          className="text-sm border border-gray-200 rounded-lg px-3 py-1.5 bg-white"
        >
          <option value="">全部类型</option>
          <option value="cluster">聚类</option>
          <option value="report">报告</option>
          <option value="health_check">健康检查</option>
          <option value="verify">验证</option>
        </select>
        <span className="text-xs text-gray-400 ml-auto">
          {offset + 1}-{Math.min(offset + limit, total)} / 共 {total} 条
        </span>
      </div>

      {loading ? (
        <div className="text-gray-400 text-center py-12">加载中...</div>
      ) : items.length === 0 ? (
        <div className="bg-white rounded-lg border border-gray-200 p-12 text-center text-gray-400">
          暂无 AI 调用记录
        </div>
      ) : (
        <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-100 bg-gray-50/50">
                  <th className="text-left px-4 py-2 text-gray-500 font-medium">Provider</th>
                  <th className="text-left px-4 py-2 text-gray-500 font-medium">任务</th>
                  <th className="text-left px-4 py-2 text-gray-500 font-medium">Model</th>
                  <th className="text-right px-4 py-2 text-gray-500 font-medium">Prompt</th>
                  <th className="text-right px-4 py-2 text-gray-500 font-medium">Completion</th>
                  <th className="text-right px-4 py-2 text-gray-500 font-medium">Total</th>
                  <th className="text-right px-4 py-2 text-gray-500 font-medium">延迟</th>
                  <th className="text-center px-4 py-2 text-gray-500 font-medium">状态</th>
                  <th className="text-left px-4 py-2 text-gray-500 font-medium">时间</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {items.map((item) => (
                  <tr key={item.id} className="hover:bg-blue-50/30 transition-colors">
                    <td className="px-4 py-2">
                      <span className={`text-xs px-2 py-0.5 rounded ${providerColor(item.provider)}`}>
                        {item.provider}
                      </span>
                    </td>
                    <td className="px-4 py-2 text-gray-700">
                      {taskLabels[item.task_type] || item.task_type}
                    </td>
                    <td className="px-4 py-2 text-gray-500 text-xs max-w-40 truncate" title={item.model}>
                      {item.model}
                    </td>
                    <td className="px-4 py-2 text-right text-gray-600">{item.prompt_tokens}</td>
                    <td className="px-4 py-2 text-right text-gray-600">{item.completion_tokens}</td>
                    <td className="px-4 py-2 text-right text-gray-900 font-medium">{item.total_tokens}</td>
                    <td className="px-4 py-2 text-right text-gray-500">{item.latency_ms}ms</td>
                    <td className="px-4 py-2 text-center">
                      {item.success ? (
                        <span className="inline-block w-2 h-2 rounded-full bg-green-400" title="成功" />
                      ) : (
                        <span className="inline-block w-2 h-2 rounded-full bg-red-400" title={item.error || "失败"} />
                      )}
                    </td>
                    <td className="px-4 py-2 text-gray-400 text-xs whitespace-nowrap">
                      {item.created_at ? new Date(item.created_at).toLocaleString("zh-CN") : "-"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {total > limit && (
            <div className="flex items-center justify-between px-4 py-3 border-t border-gray-100">
              <button
                onClick={() => setOffset(Math.max(0, offset - limit))}
                disabled={offset === 0}
                className="text-sm px-3 py-1 rounded-lg border border-gray-200 disabled:opacity-40 hover:bg-gray-50"
              >
                上一页
              </button>
              <span className="text-sm text-gray-500">
                第 {Math.floor(offset / limit) + 1} / {Math.ceil(total / limit)} 页
              </span>
              <button
                onClick={() => setOffset(offset + limit)}
                disabled={offset + limit >= total}
                className="text-sm px-3 py-1 rounded-lg border border-gray-200 disabled:opacity-40 hover:bg-gray-50"
              >
                下一页
              </button>
            </div>
          )}
        </div>
      )}

      {stats && stats.by_task.length > 0 && (
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <h3 className="text-sm font-medium text-gray-700 mb-3">按任务类型统计</h3>
          <div className="space-y-2">
            {stats.by_task.map((t) => (
              <div key={t.task_type} className="flex items-center gap-3">
                <span className="text-sm text-gray-600 w-20">{taskLabels[t.task_type] || t.task_type}</span>
                <div className="flex-1 h-6 bg-gray-100 rounded relative overflow-hidden">
                  <div
                    className="h-full bg-blue-400 rounded transition-all"
                    style={{ width: `${stats.total_calls > 0 ? (t.calls / stats.total_calls) * 100 : 0}%` }}
                  />
                </div>
                <span className="text-xs text-gray-500 w-32 text-right">
                  {t.calls} 次 / {t.tokens.toLocaleString()} tok
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
