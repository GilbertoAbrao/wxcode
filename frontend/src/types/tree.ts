/**
 * Types para a árvore hierárquica do Workspace.
 */

export type TreeNodeType =
  | "project"
  | "configuration"
  | "analysis"
  | "category"
  | "element"
  | "procedure"
  | "method"
  | "property"
  | "table"
  | "query"
  | "connection";

export interface TreeNodeMetadata {
  configId?: string;
  elementId?: string;
  configurations?: string[];
  // Para procedures/methods
  parametersCount?: number;
  returnType?: string;
  isLocal?: boolean;
  // Para tables
  columnsCount?: number;
  // Para classes
  membersCount?: number;
  methodsCount?: number;
}

export interface TreeNode {
  id: string;
  name: string;
  nodeType: TreeNodeType;
  elementType?: string;
  status?: string;
  icon?: string;
  hasChildren: boolean;
  childrenCount: number;
  children?: TreeNode[];
  metadata?: TreeNodeMetadata;
}

// Configuração de ícones por tipo de nó
export const treeNodeIcons: Record<TreeNodeType, string> = {
  project: "folder-kanban",
  configuration: "settings",
  analysis: "database",
  category: "folder",
  element: "file",
  procedure: "function-square",
  method: "function-square",
  property: "variable",
  table: "table",
  query: "search",
  connection: "plug",
};

// Configuração de ícones por elementType
export const elementTypeIcons: Record<string, string> = {
  page: "layout",
  page_template: "layout-template",
  procedure_group: "file-code",
  browser_procedure: "globe",
  class: "box",
  query: "search",
  report: "file-text",
  rest_api: "globe",
  webservice: "cloud",
};

// Labels para categorias
export const categoryLabels: Record<string, string> = {
  pages: "Pages",
  procedure_groups: "Procedure Groups",
  classes: "Classes",
  queries: "Queries",
  reports: "Reports",
  apis: "APIs",
  tables: "Tables",
  connections: "Connections",
};

// Status colors
export const statusColors: Record<string, string> = {
  pending: "bg-yellow-500",
  in_progress: "bg-blue-500",
  proposal_generated: "bg-purple-500",
  converted: "bg-green-500",
  validated: "bg-emerald-500",
  error: "bg-red-500",
  skipped: "bg-zinc-500",
};
