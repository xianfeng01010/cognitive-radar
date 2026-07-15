"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";

const navItems = [
  { href: "/", label: "最近推送" },
  { href: "/sources", label: "来源管理" },
  { href: "/health", label: "系统健康" },
  { href: "/history", label: "流量历史" },
];

export default function Nav() {
  const pathname = usePathname();
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
      </div>
    </nav>
  );
}