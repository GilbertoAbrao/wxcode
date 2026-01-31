"use client";

import { useState, useCallback, type ReactNode } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  ChevronLeft,
  ChevronRight,
  type LucideIcon,
} from "lucide-react";

export interface SidebarItem {
  id: string;
  label: string;
  href: string;
  icon: LucideIcon;
  badge?: string | number;
}

export interface SidebarSection {
  title?: string;
  items: SidebarItem[];
}

export interface SidebarProps {
  sections: SidebarSection[];
  footer?: ReactNode;
  defaultCollapsed?: boolean;
  /** External control: when provided, sidebar is controlled */
  collapsed?: boolean;
  /** Callback when collapse state changes (for controlled mode) */
  onCollapsedChange?: (collapsed: boolean) => void;
  /** Expand sidebar on mouse hover when collapsed */
  expandOnHover?: boolean;
  className?: string;
}

export function Sidebar({
  sections,
  footer,
  defaultCollapsed = false,
  collapsed: controlledCollapsed,
  onCollapsedChange,
  expandOnHover = false,
  className,
}: SidebarProps) {
  const [internalCollapsed, setInternalCollapsed] = useState(defaultCollapsed);
  const [isHovering, setIsHovering] = useState(false);
  const pathname = usePathname();

  // Use controlled state if provided, otherwise internal
  const isControlled = controlledCollapsed !== undefined;
  const actuallyCollapsed = isControlled ? controlledCollapsed : internalCollapsed;

  // Visual state: collapsed but hovering with expandOnHover shows expanded visually
  const isCollapsed = actuallyCollapsed && !(expandOnHover && isHovering);

  const toggleCollapsed = useCallback(() => {
    if (isControlled) {
      onCollapsedChange?.(!controlledCollapsed);
    } else {
      setInternalCollapsed((prev) => !prev);
    }
  }, [isControlled, controlledCollapsed, onCollapsedChange]);

  return (
    <aside
      className={`
        flex flex-col
        ${isCollapsed ? "w-16" : "w-64"}
        bg-zinc-900 border-r border-zinc-800
        transition-all duration-200
        ${className || ""}
      `}
      onMouseEnter={() => expandOnHover && setIsHovering(true)}
      onMouseLeave={() => expandOnHover && setIsHovering(false)}
    >
      {/* Collapse button */}
      <div className="flex-shrink-0 h-12 flex items-center justify-end px-2 border-b border-zinc-800">
        <button
          onClick={toggleCollapsed}
          className="p-2 rounded-lg text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800 transition-colors"
          aria-label={isCollapsed ? "Expandir sidebar" : "Recolher sidebar"}
        >
          {isCollapsed ? (
            <ChevronRight className="w-4 h-4" />
          ) : (
            <ChevronLeft className="w-4 h-4" />
          )}
        </button>
      </div>

      {/* Navigation sections */}
      <nav className="flex-1 overflow-y-auto py-4">
        {sections.map((section, sectionIndex) => (
          <div key={sectionIndex} className="mb-4">
            {/* Section title */}
            {section.title && !isCollapsed && (
              <h3 className="px-4 mb-2 text-xs font-medium text-zinc-500 uppercase tracking-wider">
                {section.title}
              </h3>
            )}

            {/* Section items */}
            <ul className="space-y-1 px-2">
              {section.items.map((item) => {
                const isActive = pathname === item.href || pathname.startsWith(`${item.href}/`);
                const Icon = item.icon;

                return (
                  <li key={item.id}>
                    <Link
                      href={item.href}
                      className={`
                        flex items-center gap-3 px-3 py-2 rounded-lg
                        transition-colors duration-150
                        ${
                          isActive
                            ? "bg-blue-600/20 text-blue-400"
                            : "text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800"
                        }
                        ${isCollapsed ? "justify-center" : ""}
                      `}
                      title={isCollapsed ? item.label : undefined}
                    >
                      <Icon className="w-5 h-5 flex-shrink-0" />

                      {!isCollapsed && (
                        <>
                          <span className="flex-1 text-sm truncate">
                            {item.label}
                          </span>

                          {item.badge !== undefined && (
                            <span className="flex-shrink-0 px-2 py-0.5 text-xs bg-zinc-700 text-zinc-300 rounded-full">
                              {item.badge}
                            </span>
                          )}
                        </>
                      )}
                    </Link>
                  </li>
                );
              })}
            </ul>
          </div>
        ))}
      </nav>

      {/* Footer */}
      {footer && (
        <div className="flex-shrink-0 p-4 border-t border-zinc-800">
          {footer}
        </div>
      )}
    </aside>
  );
}

export default Sidebar;
