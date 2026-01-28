"use client";

import { useState, useMemo, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Search, ChevronRight, ChevronDown, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { useElements, groupElementsByType } from "@/hooks/useElements";
import { staggerContainer, staggerItem, fadeInUp } from "@/lib/animations";
import type { Element, ElementGroup, ElementType } from "@/types/project";
import { elementTypeConfig } from "@/types/project";
import { ElementTreeItem } from "./ElementTreeItem";

export interface ElementTreeProps {
  projectId: string;
  selectedElementId?: string;
  onSelectElement: (element: Element) => void;
  className?: string;
}

export function ElementTree({
  projectId,
  selectedElementId,
  onSelectElement,
  className,
}: ElementTreeProps) {
  const [search, setSearch] = useState("");
  const [isFocused, setIsFocused] = useState(false);
  const [expandedGroups, setExpandedGroups] = useState<Set<ElementType>>(
    new Set(["page", "procedure", "class"])
  );

  const { data: elements, isLoading, error } = useElements(projectId, {
    search: search || undefined,
  });

  const groups = useMemo(() => {
    if (!elements) return [];
    return groupElementsByType(elements);
  }, [elements]);

  const toggleGroup = useCallback((type: ElementType) => {
    setExpandedGroups((prev) => {
      const next = new Set(prev);
      if (next.has(type)) {
        next.delete(type);
      } else {
        next.add(type);
      }
      return next;
    });
  }, []);

  const handleSelectElement = useCallback(
    (element: Element) => {
      onSelectElement(element);
    },
    [onSelectElement]
  );

  if (error) {
    return (
      <div className={cn("p-4", className)}>
        <motion.div
          variants={fadeInUp}
          initial="hidden"
          animate="visible"
          className="bg-rose-500/10 border border-rose-500/20 rounded-lg p-3"
        >
          <p className="text-sm text-rose-400">Erro ao carregar elementos</p>
        </motion.div>
      </div>
    );
  }

  return (
    <div className={cn("flex flex-col h-full", className)}>
      {/* Search with glow effect */}
      <div className="p-3 border-b border-zinc-800">
        <div className="relative">
          <Search
            className={cn(
              "absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4",
              "transition-colors duration-200",
              isFocused ? "text-blue-400" : "text-zinc-500"
            )}
          />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            onFocus={() => setIsFocused(true)}
            onBlur={() => setIsFocused(false)}
            placeholder="Buscar elementos..."
            className={cn(
              "w-full pl-9 pr-3 py-2",
              "bg-zinc-800/50 border border-zinc-700 rounded-lg",
              "text-sm text-zinc-100 placeholder:text-zinc-500",
              "focus:outline-none focus:border-blue-500/50",
              "transition-all duration-200"
            )}
            style={{
              boxShadow: isFocused
                ? "0 0 0 3px rgba(59, 130, 246, 0.15), 0 0 20px rgba(59, 130, 246, 0.1)"
                : "none",
            }}
          />
        </div>
      </div>

      {/* Tree */}
      <div className="flex-1 overflow-y-auto py-2">
        {isLoading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="w-5 h-5 text-zinc-500 animate-spin" />
          </div>
        ) : groups.length === 0 ? (
          <motion.div
            variants={fadeInUp}
            initial="hidden"
            animate="visible"
            className="px-4 py-8 text-center"
          >
            <p className="text-sm text-zinc-500">
              {search ? "Nenhum elemento encontrado" : "Nenhum elemento no projeto"}
            </p>
          </motion.div>
        ) : (
          <motion.div
            variants={staggerContainer}
            initial="hidden"
            animate="visible"
          >
            {groups.map((group) => (
              <motion.div key={group.type} variants={staggerItem}>
                <GroupSection
                  group={group}
                  isExpanded={expandedGroups.has(group.type)}
                  selectedElementId={selectedElementId}
                  onToggle={() => toggleGroup(group.type)}
                  onSelectElement={handleSelectElement}
                />
              </motion.div>
            ))}
          </motion.div>
        )}
      </div>
    </div>
  );
}

interface GroupSectionProps {
  group: ElementGroup;
  isExpanded: boolean;
  selectedElementId?: string;
  onToggle: () => void;
  onSelectElement: (element: Element) => void;
}

function GroupSection({
  group,
  isExpanded,
  selectedElementId,
  onToggle,
  onSelectElement,
}: GroupSectionProps) {
  const config = elementTypeConfig[group.type];

  return (
    <div className="mb-1">
      {/* Group header */}
      <motion.button
        onClick={onToggle}
        whileHover={{ backgroundColor: "rgba(39, 39, 42, 0.5)" }}
        className={cn(
          "w-full flex items-center gap-2 px-3 py-1.5",
          "text-zinc-400 hover:text-zinc-200",
          "transition-colors duration-150"
        )}
      >
        <motion.div
          animate={{ rotate: isExpanded ? 90 : 0 }}
          transition={{ duration: 0.2 }}
        >
          <ChevronRight className="w-4 h-4" />
        </motion.div>
        <span className="text-xs font-medium uppercase tracking-wider">
          {config.labelPlural}
        </span>
        <span className="text-xs text-zinc-500">({group.count})</span>
      </motion.button>

      {/* Group items with animation */}
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2, ease: "easeOut" }}
            className="overflow-hidden"
          >
            <div className="px-1">
              {group.elements.map((element, index) => (
                <motion.div
                  key={element.id}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.03, duration: 0.2 }}
                >
                  <ElementTreeItem
                    element={element}
                    isSelected={element.id === selectedElementId}
                    onClick={onSelectElement}
                  />
                </motion.div>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export default ElementTree;
