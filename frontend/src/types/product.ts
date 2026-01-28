/**
 * Types for Product management.
 *
 * Products are derived outputs from an imported project:
 * conversion, api, mcp, agents.
 */

// Product types matching backend ProductType enum
export type ProductType = "conversion" | "api" | "mcp" | "agents";

// Product status matching backend ProductStatus enum
export type ProductStatus =
  | "pending"
  | "in_progress"
  | "paused"
  | "completed"
  | "failed"
  | "unavailable";

// Product interface matching backend ProductResponse
export interface Product {
  id: string;
  project_id: string;
  project_name: string;
  product_type: ProductType;
  status: ProductStatus;
  workspace_path: string;
  session_id: string | null;
  output_directory: string | null;
  created_at: string;
  updated_at: string;
}

// List response from API
export interface ProductListResponse {
  products: Product[];
  total: number;
}

// Request to create a product
export interface CreateProductRequest {
  project_id: string;
  product_type: ProductType;
}

// Available product types (matches backend AVAILABLE_PRODUCT_TYPES)
export const AVAILABLE_PRODUCT_TYPES: ProductType[] = ["conversion"];

// Product status configuration for UI display
export const productStatusConfig: Record<
  ProductStatus,
  { label: string; color: string; icon: string }
> = {
  pending: { label: "Pendente", color: "yellow", icon: "clock" },
  in_progress: { label: "Em andamento", color: "blue", icon: "loader" },
  paused: { label: "Pausado", color: "orange", icon: "pause" },
  completed: { label: "Concluido", color: "green", icon: "check" },
  failed: { label: "Falhou", color: "red", icon: "x" },
  unavailable: { label: "Indisponivel", color: "gray", icon: "lock" },
};

// Product type configuration for UI display (card rendering)
export const productTypeConfig: Record<
  ProductType,
  { title: string; description: string; icon: string }
> = {
  conversion: {
    title: "Conversao FastAPI",
    description:
      "Converte o projeto WinDev para uma aplicacao FastAPI + Jinja2 moderna",
    icon: "code",
  },
  api: {
    title: "API REST",
    description:
      "Gera uma API REST documentada a partir das procedures do projeto",
    icon: "server",
  },
  mcp: {
    title: "Servidor MCP",
    description:
      "Cria um servidor MCP para integracao com Claude e outras IAs",
    icon: "cpu",
  },
  agents: {
    title: "Agentes IA",
    description:
      "Gera agentes especializados para automacao de tarefas do sistema",
    icon: "bot",
  },
};
