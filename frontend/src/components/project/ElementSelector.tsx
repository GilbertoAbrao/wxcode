"use client";

import { useState, useEffect, useMemo } from "react";
import { List, type RowComponentProps } from "react-window";
import { Search, Loader2 } from "lucide-react";
import type { BackendElement, ElementsListResponse } from "@/types/project";
import { cn } from "@/lib/utils";

export interface ElementSelectorProps {
  projectId: string;
  selectedElements: Set<string>;
  onSelectionChange: (selected: Set<string>) => void;
  isLoading?: boolean;
}

const ELEMENT_TYPE_LABELS: Record<string, string> = {
  page: "Page",
  procedure_group: "Procedure",
  class: "Class",
  query: "Query",
  report: "Report",
  rest_api: "REST API",
  webservice: "Webservice",
  unknown: "Unknown",
};

const LAYER_LABELS: Record<string, string> = {
  schema: "Schema",
  domain: "Domain",
  business: "Business",
  api: "API",
  ui: "UI",
};

export function ElementSelector({
  projectId,
  selectedElements,
  onSelectionChange,
  isLoading: parentLoading = false,
}: ElementSelectorProps) {
  const [elements, setElements] = useState<BackendElement[]>([]);
  const [isLoadingElements, setIsLoadingElements] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [searchTerm, setSearchTerm] = useState("");
  const [typeFilter, setTypeFilter] = useState<string>("all");
  const [layerFilter, setLayerFilter] = useState<string>("all");

  // Fetch elements
  useEffect(() => {
    async function fetchElements() {
      setIsLoadingElements(true);
      setError(null);

      try {
        const response = await fetch(
          `/api/elements/?project_id=${projectId}&limit=1000`
        );

        if (!response.ok) throw new Error("Failed to fetch elements");

        const data: ElementsListResponse = await response.json();
        setElements(data.elements);
      } catch (err) {
        console.error("Error fetching elements:", err);
        setError("Erro ao carregar elementos");
      } finally {
        setIsLoadingElements(false);
      }
    }

    if (projectId) {
      fetchElements();
    }
  }, [projectId]);

  // Filtered elements
  const filteredElements = useMemo(() => {
    return elements.filter((el) => {
      // Search filter
      if (searchTerm && !el.source_name.toLowerCase().includes(searchTerm.toLowerCase())) {
        return false;
      }

      // Type filter
      if (typeFilter !== "all" && el.source_type !== typeFilter) {
        return false;
      }

      // Layer filter
      if (layerFilter !== "all" && el.layer !== layerFilter) {
        return false;
      }

      return true;
    });
  }, [elements, searchTerm, typeFilter, layerFilter]);

  const handleToggle = (elementName: string) => {
    const newSelected = new Set(selectedElements);
    if (newSelected.has(elementName)) {
      newSelected.delete(elementName);
    } else {
      newSelected.add(elementName);
    }
    onSelectionChange(newSelected);
  };

  const handleSelectAll = () => {
    const allNames = new Set(filteredElements.map((e) => e.source_name));
    onSelectionChange(allNames);
  };

  const handleClearAll = () => {
    onSelectionChange(new Set());
  };

  const isDisabled = parentLoading || isLoadingElements;

  // Row renderer for virtual list (react-window v2 API)
  interface ElementRowProps {
    elements: BackendElement[];
    selectedElements: Set<string>;
    onToggle: (name: string) => void;
    isDisabled: boolean;
  }

  const ElementRow = ({ elements, selectedElements, onToggle, isDisabled, index }: RowComponentProps<ElementRowProps>) => {
    const element = elements[index];
    if (!element) return null;

    const isSelected = selectedElements.has(element.source_name);

    return (
      <div className="px-2">
        <label
          className={cn(
            "flex items-center gap-3 p-3 rounded-lg cursor-pointer transition-colors",
            "hover:bg-zinc-800",
            isSelected && "bg-zinc-800"
          )}
        >
          <input
            type="checkbox"
            checked={isSelected}
            onChange={() => onToggle(element.source_name)}
            disabled={isDisabled}
            className="w-4 h-4 rounded border-zinc-600 text-blue-600 focus:ring-blue-500"
          />

          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <span className="text-sm font-medium text-zinc-100 truncate">
                {element.source_name}
              </span>

              <span className="px-2 py-0.5 text-xs bg-zinc-700 text-zinc-300 rounded">
                {ELEMENT_TYPE_LABELS[element.source_type] || element.source_type}
              </span>

              {element.layer && (
                <span className="px-2 py-0.5 text-xs bg-blue-900/50 text-blue-300 rounded">
                  {LAYER_LABELS[element.layer]}
                </span>
              )}
            </div>

            <div className="flex items-center gap-3 text-xs text-zinc-500">
              <span className="truncate">{element.source_file}</span>
              <span>↑{element.dependencies_count}</span>
              <span>↓{element.dependents_count}</span>
            </div>
          </div>
        </label>
      </div>
    );
  };

  if (isLoadingElements) {
    return (
      <div className="flex items-center justify-center py-8">
        <Loader2 className="w-6 h-6 text-zinc-500 animate-spin" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-8">
        <p className="text-sm text-rose-400">{error}</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {/* Filters */}
      <div className="flex items-center gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
          <input
            type="text"
            placeholder="Buscar por nome..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            disabled={isDisabled}
            className={cn(
              "w-full pl-10 pr-4 py-2 rounded-lg text-sm",
              "bg-zinc-900 border border-zinc-700",
              "focus:border-blue-500 outline-none",
              "placeholder:text-zinc-500",
              "disabled:opacity-50 disabled:cursor-not-allowed"
            )}
          />
        </div>

        <select
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
          disabled={isDisabled}
          className="px-3 py-2 rounded-lg text-sm bg-zinc-900 border border-zinc-700 focus:border-blue-500 outline-none"
        >
          <option value="all">Todos os tipos</option>
          <option value="page">Pages</option>
          <option value="procedure_group">Procedures</option>
          <option value="class">Classes</option>
          <option value="query">Queries</option>
        </select>

        <select
          value={layerFilter}
          onChange={(e) => setLayerFilter(e.target.value)}
          disabled={isDisabled}
          className="px-3 py-2 rounded-lg text-sm bg-zinc-900 border border-zinc-700 focus:border-blue-500 outline-none"
        >
          <option value="all">Todas as layers</option>
          <option value="schema">Schema</option>
          <option value="domain">Domain</option>
          <option value="business">Business</option>
          <option value="api">API</option>
          <option value="ui">UI</option>
        </select>
      </div>

      {/* Actions */}
      <div className="flex items-center justify-between">
        <span className="text-sm text-zinc-400">
          {selectedElements.size} de {filteredElements.length} selecionados
        </span>

        <div className="flex gap-2">
          <button
            type="button"
            onClick={handleSelectAll}
            disabled={isDisabled}
            className="text-xs text-blue-400 hover:text-blue-300 disabled:opacity-50"
          >
            Selecionar todos
          </button>
          <span className="text-zinc-700">|</span>
          <button
            type="button"
            onClick={handleClearAll}
            disabled={isDisabled}
            className="text-xs text-zinc-400 hover:text-zinc-300 disabled:opacity-50"
          >
            Limpar
          </button>
        </div>
      </div>

      {/* Virtual List */}
      <div className="border border-zinc-800 rounded-lg overflow-hidden">
        {filteredElements.length > 0 ? (
          <List
            defaultHeight={300}
            rowCount={filteredElements.length}
            rowHeight={60}
            rowComponent={ElementRow}
            rowProps={{
              elements: filteredElements,
              selectedElements: selectedElements,
              onToggle: handleToggle,
              isDisabled: isDisabled,
            }}
            style={{ height: 300 }}
          />
        ) : (
          <div className="py-8 text-center text-sm text-zinc-500">
            Nenhum elemento encontrado
          </div>
        )}
      </div>
    </div>
  );
}
