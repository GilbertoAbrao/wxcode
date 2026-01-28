/**
 * Types compartilhados para o sistema de projetos e conversões.
 */

// Element types
export type ElementType = "page" | "procedure" | "class" | "query" | "table";

export type ElementStatus = "pending" | "converting" | "converted" | "error";

export interface Element {
  id: string;
  name: string;
  type: ElementType;
  status: ElementStatus;
  sourceFile?: string;
  lines?: number;
  dependencies?: number;  // Quantidade que este USA
  dependents?: number;    // Quantidade que USAM este
  dependencyNames?: string[];  // Nomes dos elementos que este usa
  children?: Element[];
}

// Project Configuration (from WinDev build config)
export interface ProjectConfiguration {
  name: string;
  configuration_id: string;
  config_type: number;
  generation_directory?: string;
  generation_name?: string;
  version?: string;
}

// Project types
export interface Project {
  id: string;
  name: string;
  display_name?: string;      // Original name without workspace suffix
  workspace_id?: string;      // 8-char hex workspace ID
  workspace_path?: string;    // Full path to workspace directory
  description?: string;
  configurations?: ProjectConfiguration[];  // WinDev build configurations
  elementsCount: number;
  conversionsCount: number;
  lastActivity: Date;
  tokenUsage: {
    total: number;
    cost: number;
  };
  createdAt: Date;
  updatedAt: Date;
}

// Conversion types
export type ConversionStatus =
  | "pending"
  | "in_progress"
  | "review"
  | "completed"
  | "failed";

export interface Conversion {
  id: string;
  projectId: string;
  name: string;
  description?: string;
  status: ConversionStatus;
  elementsTotal: number;
  elementsConverted: number;
  tokensUsed: number;
  elements?: ConversionElement[];
  createdAt: Date;
  updatedAt: Date;
}

export interface ConversionElement {
  id: string;
  elementId: string;
  elementName: string;
  elementType: ElementType;
  status: "pending" | "converted" | "error";
  originalCode?: string;
  convertedCode?: string;
}

// Element groups for tree display
export interface ElementGroup {
  type: ElementType;
  label: string;
  elements: Element[];
  count: number;
}

// Backend Element types
export type BackendElementType =
  | "page"
  | "page_template"
  | "procedure_group"
  | "browser_procedure"
  | "class"
  | "query"
  | "report"
  | "rest_api"
  | "webservice"
  | "unknown";

export type BackendElementLayer =
  | "schema"
  | "domain"
  | "business"
  | "api"
  | "ui";

export type BackendConversionStatus =
  | "pending"
  | "in_progress"
  | "proposal_generated"
  | "converted"
  | "validated"
  | "error"
  | "skipped";

export interface BackendElement {
  id: string;
  source_type: BackendElementType;
  source_name: string;
  source_file: string;
  layer: BackendElementLayer | null;
  topological_order: number | null;
  conversion_status: BackendConversionStatus;
  has_chunks: boolean;
  dependencies_count: number;
  dependents_count: number;
  dependencies_uses: string[];
}

export interface ElementsListResponse {
  elements: BackendElement[];
  total: number;
}

// CreateConversionData
export interface CreateConversionData {
  name: string;
  description?: string;
  targetStack?: string;
  layer?: string;
  elementNames?: string[];
}

// Status labels and colors
export const elementStatusConfig: Record<
  ElementStatus,
  { label: string; color: string }
> = {
  pending: { label: "Pendente", color: "yellow" },
  converting: { label: "Convertendo", color: "blue" },
  converted: { label: "Convertido", color: "green" },
  error: { label: "Erro", color: "red" },
};

export const conversionStatusConfig: Record<
  ConversionStatus,
  { label: string; color: string; icon: string }
> = {
  pending: { label: "Pendente", color: "yellow", icon: "clock" },
  in_progress: { label: "Em andamento", color: "blue", icon: "loader" },
  review: { label: "Em revisão", color: "purple", icon: "eye" },
  completed: { label: "Concluído", color: "green", icon: "check" },
  failed: { label: "Falhou", color: "red", icon: "x" },
};

export const elementTypeConfig: Record<
  ElementType,
  { label: string; labelPlural: string; icon: string }
> = {
  page: { label: "Página", labelPlural: "Páginas", icon: "layout" },
  procedure: { label: "Procedure", labelPlural: "Procedures", icon: "code" },
  class: { label: "Classe", labelPlural: "Classes", icon: "box" },
  query: { label: "Query", labelPlural: "Queries", icon: "database" },
  table: { label: "Tabela", labelPlural: "Tabelas", icon: "table" },
};

// Delete project types
export interface DeleteProjectStats {
  project_name: string;
  projects: number;
  elements: number;
  controls: number;
  procedures: number;
  class_definitions: number;
  schemas: number;
  conversions: number;
  total: number;
  files_deleted: number;
  directories_deleted: number;
  total_files: number;
  neo4j_nodes?: number;
  neo4j_error?: string;
  files_error?: string;
}

export interface DeleteProjectResponse {
  message: string;
  stats: DeleteProjectStats;
}
