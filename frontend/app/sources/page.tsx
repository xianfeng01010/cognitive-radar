export default function Sources() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">来源管理</h1>
        <p className="text-gray-500 text-sm mt-1">订阅源列表 + 信任分 + 缓存池状态</p>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h2 className="font-semibold text-lg mb-2">L1 核心订阅</h2>
          <p className="text-3xl font-bold text-blue-600">0</p>
          <p className="text-gray-400 text-sm mt-1">预设 / 晋升的高质量源</p>
        </div>
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h2 className="font-semibold text-lg mb-2">L2 候选订阅</h2>
          <p className="text-3xl font-bold text-amber-600">0</p>
          <p className="text-gray-400 text-sm mt-1">拓展搜索发现的候选源</p>
        </div>
      </div>

      <div className="bg-white rounded-lg border border-gray-200 p-12 text-center text-gray-400">
        来源详情开发中...
      </div>
    </div>
  );
}