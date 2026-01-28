"use client";

import { type ReactNode } from "react";
import Link from "next/link";
import { ChevronRight, Zap } from "lucide-react";

export interface BreadcrumbItem {
  label: string;
  href?: string;
}

export interface HeaderProps {
  breadcrumbs?: BreadcrumbItem[];
  children?: ReactNode;
  className?: string;
}

export function Header({ breadcrumbs, children, className }: HeaderProps) {
  return (
    <header
      className={`
        h-14 px-4
        flex items-center justify-between
        bg-zinc-900 border-b border-zinc-800
        ${className || ""}
      `}
    >
      {/* Left side: Logo + Breadcrumbs */}
      <div className="flex items-center gap-4">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2 group">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
            <Zap className="w-4 h-4 text-white" />
          </div>
          <span className="font-semibold text-zinc-100 group-hover:text-white transition-colors">
            WXCODE
          </span>
        </Link>

        {/* Breadcrumbs */}
        {breadcrumbs && breadcrumbs.length > 0 && (
          <nav className="flex items-center gap-1">
            <ChevronRight className="w-4 h-4 text-zinc-600" />
            {breadcrumbs.map((item, index) => (
              <div key={index} className="flex items-center gap-1">
                {item.href ? (
                  <Link
                    href={item.href}
                    className="text-sm text-zinc-400 hover:text-zinc-200 transition-colors"
                  >
                    {item.label}
                  </Link>
                ) : (
                  <span className="text-sm text-zinc-300">{item.label}</span>
                )}
                {index < breadcrumbs.length - 1 && (
                  <ChevronRight className="w-4 h-4 text-zinc-600" />
                )}
              </div>
            ))}
          </nav>
        )}
      </div>

      {/* Right side: Actions */}
      {children && (
        <div className="flex items-center gap-2">{children}</div>
      )}
    </header>
  );
}

export default Header;
