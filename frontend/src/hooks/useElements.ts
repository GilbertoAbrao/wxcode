"use client";

/**
 * Hook para buscar elementos de um projeto.
 * Usa mock data como fallback quando a API não está disponível.
 */

import { useQuery } from "@tanstack/react-query";
import type { Element, ElementType, ElementStatus, ElementGroup } from "@/types/project";
import { elementTypeConfig } from "@/types/project";
import { mockElements, getMockElementCode } from "@/lib/mock-data";

const USE_MOCK = process.env.NEXT_PUBLIC_USE_MOCK === "true";

interface UseElementsOptions {
  type?: ElementType;
  status?: ElementStatus;
  search?: string;
}

// Backend response type (from /api/elements endpoint)
interface BackendElement {
  id: string;
  source_type: string;
  source_name: string;
  source_file?: string;
  conversion_status?: string;
  dependencies_count?: number;
  dependents_count?: number;
  dependencies_uses?: string[];  // Nomes dos elementos que este usa
}

// Map backend source_type to frontend ElementType
function mapSourceType(sourceType: string): ElementType {
  const mapping: Record<string, ElementType> = {
    page: "page",
    procedure_group: "procedure",
    class: "class",
    query: "query",
    table: "table",
    browser_procedure: "procedure",
    webservice: "procedure",
    page_template: "page",
    report: "page",
    rest_api: "procedure",
  };
  return mapping[sourceType] || "procedure";
}

function adaptElement(data: BackendElement): Element {
  return {
    id: data.id,
    name: data.source_name,
    type: mapSourceType(data.source_type),
    status: (data.conversion_status as ElementStatus) || "pending",
    sourceFile: data.source_file,
    dependencies: data.dependencies_count || 0,
    dependents: data.dependents_count || 0,
    dependencyNames: data.dependencies_uses || [],
  };
}

async function fetchElements(
  projectId: string,
  options?: UseElementsOptions
): Promise<Element[]> {
  if (USE_MOCK) {
    await new Promise((resolve) => setTimeout(resolve, 400));
    let elements = mockElements[projectId] || [];

    if (options?.type) {
      elements = elements.filter((el) => el.type === options.type);
    }
    if (options?.status) {
      elements = elements.filter((el) => el.status === options.status);
    }
    if (options?.search) {
      const search = options.search.toLowerCase();
      elements = elements.filter((el) =>
        el.name.toLowerCase().includes(search)
      );
    }

    return elements;
  }

  // Backend uses project_name, we need to fetch project first or use ID
  // For now, try the elements endpoint with project_id filter
  const params = new URLSearchParams();
  params.set("project_id", projectId);
  params.set("limit", "500");
  if (options?.type) params.set("source_type", options.type);
  if (options?.search) params.set("search", options.search);

  try {
    const response = await fetch(`/api/elements?${params}`);
    if (!response.ok) {
      // Fallback to empty array if endpoint fails
      console.warn("Elements endpoint failed, returning empty array");
      return [];
    }
    const data = await response.json();
    const elements: BackendElement[] = data.elements || data || [];
    return elements.map(adaptElement);
  } catch (error) {
    console.error("Failed to fetch elements:", error);
    return [];
  }
}

async function fetchElement(
  projectId: string,
  elementId: string
): Promise<Element & { code?: string }> {
  if (USE_MOCK) {
    await new Promise((resolve) => setTimeout(resolve, 200));
    const elements = mockElements[projectId] || [];
    const element = elements.find((el) => el.id === elementId);
    if (!element) {
      throw new Error("Element not found");
    }
    return {
      ...element,
      code: getMockElementCode(elementId),
    };
  }

  // Backend endpoint é /api/elements/{element_id}
  const response = await fetch(`/api/elements/${elementId}`);
  if (!response.ok) {
    throw new Error("Failed to fetch element");
  }

  // Adapta resposta do backend para o formato do frontend
  const data = await response.json();
  return {
    id: data.id,
    name: data.source_name,
    type: mapSourceType(data.source_type),
    status: (data.conversion_status as ElementStatus) || "pending",
    sourceFile: data.source_file,
    lines: 0,
    dependencies: data.dependencies_count || 0,
    code: data.raw_content,
  };
}

export function useElements(projectId: string, options?: UseElementsOptions) {
  return useQuery({
    queryKey: ["elements", projectId, options],
    queryFn: () => fetchElements(projectId, options),
    enabled: !!projectId,
  });
}

export function useElement(projectId: string, elementId: string) {
  return useQuery({
    queryKey: ["element", projectId, elementId],
    queryFn: () => fetchElement(projectId, elementId),
    enabled: !!projectId && !!elementId,
  });
}

/**
 * Agrupa elementos por tipo para exibição na árvore.
 */
export function groupElementsByType(elements: Element[]): ElementGroup[] {
  const groups: Record<ElementType, Element[]> = {
    page: [],
    procedure: [],
    class: [],
    query: [],
    table: [],
  };

  for (const element of elements) {
    if (groups[element.type]) {
      groups[element.type].push(element);
    }
  }

  return (Object.entries(groups) as [ElementType, Element[]][])
    .filter(([, items]) => items.length > 0)
    .map(([type, items]) => ({
      type,
      label: elementTypeConfig[type].labelPlural,
      elements: items,
      count: items.length,
    }));
}

// ============================================================================
// Raw API types and hook for conversion wizard
// ============================================================================

/**
 * Raw element from backend API.
 * Used by conversion wizard to show elements with their backend types.
 */
export interface RawElement {
  id: string;
  source_type: string;
  source_name: string;
  source_file: string;
  layer: string | null;
  topological_order: number | null;
  conversion_status: string;
  has_chunks: boolean;
  dependencies_count: number;
  dependents_count: number;
  dependencies_uses: string[];
}

interface RawElementListResponse {
  elements: RawElement[];
  total: number;
}

interface UseElementsRawOptions {
  sourceType?: string;
  layer?: string;
  status?: string;
  skip?: number;
  limit?: number;
}

/**
 * Fetch elements for a project (raw API response).
 *
 * Unlike useElements which adapts the response to frontend types,
 * this hook returns the raw backend response with total count.
 * Used by conversion wizard for element selection.
 *
 * @param projectId - MongoDB ObjectId of the project (NOT the URL slug)
 * @param options - Filter and pagination options
 */
export function useElementsRaw(
  projectId: string,
  options: UseElementsRawOptions = {}
) {
  const { sourceType, layer, status, skip = 0, limit = 100 } = options;

  return useQuery({
    queryKey: ["elementsRaw", projectId, options],
    queryFn: async (): Promise<RawElementListResponse> => {
      const params = new URLSearchParams();
      params.set("project_id", projectId);
      if (sourceType) params.set("source_type", sourceType);
      if (layer) params.set("layer", layer);
      if (status) params.set("status", status);
      params.set("skip", skip.toString());
      params.set("limit", limit.toString());

      const response = await fetch(`/api/elements?${params.toString()}`);
      if (!response.ok) {
        throw new Error("Failed to fetch elements");
      }
      return response.json();
    },
    enabled: !!projectId,
    staleTime: 30000, // 30 seconds
  });
}
