import type { Metadata } from "next";
import "./globals.css";
import Link from "next/link";

export const metadata: Metadata = {
  title: "认知雷达",
  description: "Search-driven self-growing information network",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh">
      <body className="bg-gray-50 min-h-screen">
        <nav className="bg-white border-b border-gray-200 px-6 py-3">
          <div className="max-w-6xl mx-auto flex items-center gap-6">
            <Link href="/" className="font-bold text-lg text-gray-900">
              📡 认知雷达
            </Link>
            <Link href="/" className="text-gray-600 hover:text-gray-900 text-sm">
              最近推送
            </Link>
            <Link href="/sources" className="text-gray-600 hover:text-gray-900 text-sm">
              来源管理
            </Link>
            <Link href="/health" className="text-gray-600 hover:text-gray-900 text-sm">
              系统健康
            </Link>
            <Link href="/history" className="text-gray-600 hover:text-gray-900 text-sm">
              流量历史
            </Link>
          </div>
        </nav>
        <main className="max-w-6xl mx-auto px-6 py-8">{children}</main>
      </body>
    </html>
  );
}