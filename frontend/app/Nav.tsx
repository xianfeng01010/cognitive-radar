"use client";
import { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { api } from "@/lib/api";

const navItems = [
  { href: "/", label: "最近推送" },
  { href: "/sources", label: "来源管理" },
  { href: "/health", label: "系统健康" },
  { href: "/history", label: "流量历史" },
  { href: "/ai-usage", label: "AI用量" },
];

export default function Nav() {
  const pathname = usePathname();
  const [providers, setProviders] = useState<any[]>([]);
  const [current, setCurrent] = useState("");
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [switching, setSwitching] = useState(false);

  const fetchProvider = async () => {
    try {
      const data = await api.getLLMProvider();
      setProviders(data.providers || []);
      setCurrent(data.current || "");
    } catch {
      // ignore
    }
  };

  useEffect(() => {
    fetchProvider();
    const interval = setInterval(fetchProvider, 30000);
    return () => clearInterval(interval);
  }, []);

  const switchProvider = async (name: string) => {
    if (name === current || switching) return;
    setSwitching(true);
    try {
      const data = await api.switchLLMProvider(name);
      setCurrent(data.current);
      setProviders(data.providers || []);
    } catch (e) {
      alert(e instanceof Error ? e.message : "切换失败");
    } finally {
      setSwitching(false);
      setDropdownOpen(false);
    }
  };

  return (
    <nav className="sticky top-0 z-40 backdrop-blur-md bg-white/80 border-b border-gray-200/60 shadow-sm">
      <div className="max-w-6xl mx-auto flex items-center gap-1 px-6 py-3">
        <Link href="/" className="font-bold text-lg text-gray-900 mr-6 flex items-center gap-1.5">
          <span className="inline-block w-2.5 h-2.5 rounded-full bg-blue-500 animate-pulse-soft" />
          认知雷达
        </Link>
        {navItems.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`nav-link text-sm px-2 py-1 rounded transition-colors ${
                isActive
                  ? "text-gray-900 font-medium active"
                  : "text-gray-500 hover:text-gray-900"
              }`}
            >
              {item.label}
            </Link>
          );
        })}

        <div className="ml-auto relative">
          <button
            onClick={() => setDropdownOpen(!dropdownOpen)}
            className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg border border-gray-200 bg-white hover:bg-gray-50 transition-colors"
          >
            <span className={`inline-block w-2 h-2 rounded-full ${switching ? "bg-amber-400 animate-pulse" : "bg-green-400"}`} />
            <span className="text-gray-700 font-medium">{current || "未设置"}</span>
            <svg className="w-3 h-3 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>

          {dropdownOpen && (
            <>
              <div className="fixed inset-0 z-40" onClick={() => setDropdownOpen(false)} />
              <div className="absolute right-0 mt-1 w-56 bg-white border border-gray-200 rounded-lg shadow-lg z-50 overflow-hidden">
                <div className="px-3 py-2 text-xs text-gray-400 border-b border-gray-100">LLM Provider</div>
                {providers.map((p) => (
                  <button
                    key={p.name}
                    onClick={() => switchProvider(p.name)}
                    disabled={!p.available || switching}
                    className={`w-full flex items-center justify-between px-3 py-2 text-sm transition-colors ${
                      p.is_current
                        ? "bg-blue-50 text-blue-700 font-medium"
                        : "hover:bg-gray-50 text-gray-700"
                    } ${!p.available ? "opacity-40 cursor-not-allowed" : ""}`}
                  >
                    <span className="flex items-center gap-2">
                      <span className={`w-1.5 h-1.5 rounded-full ${p.is_current ? "bg-blue-500" : "bg-gray-300"}`} />
                      {p.name}
                    </span>
                    <span className="text-xs text-gray-400 truncate max-w-28">{p.model || "—"}</span>
                  </button>
                ))}
                {!providers.some((p) => p.available && !p.is_current) && (
                  <div className="px-3 py-2 text-xs text-gray-400">无其他可用 Provider</div>
                )}
              </div>
            </>
          )}
        </div>
      </div>
    </nav>
  );
}
