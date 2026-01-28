"use client";

import { useState, useMemo } from "react";
import { motion } from "framer-motion";
import { Check, Search, FileCode, Database, Layers } from "lucide-react";
import { cn } from "@/lib/utils";
import type { RawElement } from "@/hooks/useElements";

// Icon mapping for element types
const TYPE_ICONS: Record<string, React.ComponentType<{ className?: string }>> = {
  page: FileCode,
  procedure: Layers,
  procedure_group: Layers,
  class: Database,
  query: Database,
  report: FileCode,
};

// Color mapping for element types
const TYPE_COLORS: Record<string, string> = {
  page: "text-blue-400",
  procedure: "text-purple-400",
  procedure_group: "text-purple-400",
  class: "text-emerald-400",
  query: "text-amber-400",
  report: "text-pink-400",
};

interface ElementSelectorProps {
  elements: RawElement[];
  selectedElements: string[];
  onSelectionChange: (elements: string[]) => void;
  isLoading?: boolean;
  maxSelections?: number;
}

export function ElementSelector({
  elements,
  selectedElements,
  onSelectionChange,
  isLoading = false,
  maxSelections = 1, // Start with single element (per research recommendation)
}: ElementSelectorProps) {
  const [search, setSearch] = useState("");

  // Filter elements by search
  const filteredElements = useMemo(() => {
    if (!search) return elements;
    const searchLower = search.toLowerCase();
    return elements.filter(
      (el) =>
        el.source_name.toLowerCase().includes(searchLower) ||
        el.source_type.toLowerCase().includes(searchLower)
    );
  }, [elements, search]);

  // Toggle element selection
  const toggleElement = (elementName: string) => {
    if (selectedElements.includes(elementName)) {
      onSelectionChange(selectedElements.filter((e) => e !== elementName));
    } else {
      if (maxSelections === 1) {
        // Single selection mode
        onSelectionChange([elementName]);
      } else if (selectedElements.length < maxSelections) {
        // Multi-selection with limit
        onSelectionChange([...selectedElements, elementName]);
      }
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-3">
        {[1, 2, 3, 4, 5].map((i) => (
          <div
            key={i}
            className="h-16 bg-zinc-900 rounded-lg animate-pulse"
          />
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-400" />
        <input
          type="text"
          placeholder="Buscar elementos..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full pl-10 pr-4 py-2.5 bg-zinc-900 border border-zinc-800 rounded-lg text-sm text-zinc-100 placeholder:text-zinc-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500"
        />
      </div>

      {/* Element list */}
      <div className="space-y-2 max-h-96 overflow-y-auto pr-1">
        {filteredElements.length === 0 ? (
          <div className="text-center py-8 text-zinc-500">
            {search ? "Nenhum elemento encontrado" : "Nenhum elemento disponivel"}
          </div>
        ) : (
          filteredElements.map((element) => {
            const Icon = TYPE_ICONS[element.source_type] || FileCode;
            const iconColor = TYPE_COLORS[element.source_type] || "text-zinc-400";
            const isSelected = selectedElements.includes(element.source_name);

            return (
              <motion.button
                key={element.id}
                onClick={() => toggleElement(element.source_name)}
                whileHover={{ scale: 1.01 }}
                whileTap={{ scale: 0.99 }}
                className={cn(
                  "w-full p-3 text-left rounded-lg border transition-all",
                  isSelected
                    ? "bg-blue-500/10 border-blue-500/50 ring-1 ring-blue-500/30"
                    : "bg-zinc-900 border-zinc-800 hover:border-zinc-700"
                )}
              >
                <div className="flex items-center gap-3">
                  {/* Selection checkbox */}
                  <div
                    className={cn(
                      "w-5 h-5 rounded border flex items-center justify-center flex-shrink-0",
                      isSelected
                        ? "bg-blue-500 border-blue-500"
                        : "border-zinc-700"
                    )}
                  >
                    {isSelected && <Check className="w-3 h-3 text-white" />}
                  </div>

                  {/* Icon */}
                  <Icon className={cn("w-5 h-5 flex-shrink-0", iconColor)} />

                  {/* Element info */}
                  <div className="flex-1 min-w-0">
                    <div className="font-medium text-zinc-100 truncate">
                      {element.source_name}
                    </div>
                    <div className="flex items-center gap-2 text-xs text-zinc-500">
                      <span>{element.source_type}</span>
                      {element.layer && (
                        <>
                          <span>-</span>
                          <span>{element.layer}</span>
                        </>
                      )}
                      {element.dependencies_count > 0 && (
                        <>
                          <span>-</span>
                          <span>{element.dependencies_count} deps</span>
                        </>
                      )}
                    </div>
                  </div>

                  {/* Status badge */}
                  <div
                    className={cn(
                      "px-2 py-0.5 text-xs rounded-full",
                      element.conversion_status === "pending"
                        ? "bg-zinc-800 text-zinc-400"
                        : element.conversion_status === "converted"
                        ? "bg-emerald-500/20 text-emerald-400"
                        : "bg-amber-500/20 text-amber-400"
                    )}
                  >
                    {element.conversion_status === "pending"
                      ? "Pendente"
                      : element.conversion_status === "converted"
                      ? "Convertido"
                      : element.conversion_status}
                  </div>
                </div>
              </motion.button>
            );
          })
        )}
      </div>

      {/* Selection summary */}
      <div className="flex items-center justify-between text-sm text-zinc-400 pt-2 border-t border-zinc-800">
        <span>
          {selectedElements.length} de {maxSelections} elemento(s) selecionado(s)
        </span>
        <span className="text-zinc-500">
          {filteredElements.length} elemento(s) disponiveis
        </span>
      </div>
    </div>
  );
}

export default ElementSelector;
