"use client";
import { useState, useEffect } from "react";
import { api } from "@/lib/api";

export default function Health() {
  const [health, setHealth] = useState<any>(null);
  const [report, setReport] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    try {
      const [h, r] = await Promise.all([
        api.systemHealth().catch(() => null),
        api.healthReport(1).catch(() => null),
      ]);
      setHealth(h);
      setReport(r?.reports?.[0] || null);
    } finally { setLoading(false); }
  };

  useEffect(() => { load(); }, []);

  const statusColor = (s: string) => {
    if (s?.includes("healthy")) return "bg-green-100 text-green-700";
    if (s?.includes("unhealthy")) return "bg-red-100 text-red-700";
    return "bg-gray-100 text-gray-600";
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">系统健康</h1>
        <p className="text-gray-500 text-sm mt-1">组件状态 + 周报</p>
      </div>

      {loading ? (
        <div className="text-gray-400 text-center py-12">加载中...</div>
      ) : (
        <>
          {/* Component health */}
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <div className="flex items-center gap-3 mb-4">
              <h2 className="font-semibold text-lg">组件状态</h2>
              <span className={`text-xs px-2 py-1 rounded ${statusColor(health?.status || "")}`}>
                {health?.status || "unknown"}
              </span>
            </div>
            <div className="grid grid-cols-3 gap-3">
              {health?.components && Object.entries(health.components).map(([name, status]: [string, any]) => (
                <div key={name} className="border border-gray-200 rounded-lg p-3">
                  <div className="text-xs text-gray-500">{name}</div>
                  <div className={`text-sm font-medium mt-1 ${status.includes("healthy") ? "text-green-600" : "text-red-600"}`}>
                    {status}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Health report */}
          {report ? (
            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <h2 className="font-semibold text-lg mb-4">最近报告</h2>
              <div className="grid grid-cols-2 gap-4 text-sm">
                {report.report_data?.sources && (
                  <div>
                    <h3 className="font-medium text-gray-700 mb-1">订阅源</h3>
                    <p>活跃: {report.report_data.sources.total_active}</p>
                    <p>L1核心: {report.report_data.sources.l1_core}</p>
                    <p>L2候选: {report.report_data.sources.l2_candidate}</p>
                    <p>过期: {report.report_data.sources.expired}</p>
                  </div>
                )}
                {report.report_data?.activity && (
                  <div>
                    <h3 className="font-medium text-gray-700 mb-1">活动</h3>
                    <p>推送: {report.report_data.activity.weekly_pushes}</p>
                    <p>搜索: {report.report_data.activity.weekly_searches}</p>
                    <p>浏览: {report.report_data.activity.weekly_views}</p>
                  </div>
                )}
                {report.report_data?.buffer && (
                  <div>
                    <h3 className="font-medium text-gray-700 mb-1">缓冲池</h3>
                    <p>待验证: {report.report_data.buffer.pending}</p>
                    <p>已验证: {report.report_data.buffer.verified}</p>
                  </div>
                )}
                {report.report_data?.feedback && (
                  <div>
                    <h3 className="font-medium text-gray-700 mb-1">反馈</h3>
                    <p className="text-green-600">👍 {report.report_data.feedback.likes}</p>
                    <p className="text-red-600">👎 {report.report_data.feedback.dislikes}</p>
                  </div>
                )}
              </div>
              {report.created_at && (
                <p className="text-xs text-gray-400 mt-4">
                  生成时间: {new Date(report.created_at).toLocaleString("zh-CN")}
                </p>
              )}
            </div>
          ) : (
            <div className="bg-white rounded-lg border border-gray-200 p-12 text-center text-gray-400">
              暂无健康报告
            </div>
          )}
        </>
      )}
    </div>
  );
}