/**
 * Mock data para desenvolvimento quando a API não está disponível.
 * Ativado via NEXT_PUBLIC_USE_MOCK=true no .env.local
 */

import type {
  Project,
  Element,
  Conversion,
  ConversionElement,
} from "@/types/project";
import type { TokenUsageResponse } from "@/hooks/useTokenUsage";

// ── Projects ──────────────────────────────────────────────────────────

export const mockProjects: Project[] = [
  {
    id: "proj_1",
    name: "Linkpay_ADM",
    display_name: "Linkpay ADM",
    description: "Sistema administrativo Linkpay",
    elementsCount: 42,
    conversionsCount: 3,
    lastActivity: new Date("2025-01-15"),
    tokenUsage: { total: 125000, cost: 1.25 },
    createdAt: new Date("2025-01-01"),
    updatedAt: new Date("2025-01-15"),
  },
];

// ── Elements ──────────────────────────────────────────────────────────

export const mockElements: Record<string, Element[]> = {
  proj_1: [
    { id: "el_1", name: "PAGE_Login", type: "page", status: "converted", sourceFile: "PAGE_Login.wwh", lines: 350, dependencies: 3, dependents: 1 },
    { id: "el_2", name: "PAGE_Principal", type: "page", status: "pending", sourceFile: "PAGE_Principal.wwh", lines: 1200, dependencies: 8, dependents: 0 },
    { id: "el_3", name: "classUsuario", type: "class", status: "converted", sourceFile: "classUsuario.wdc", lines: 200, dependencies: 2, dependents: 5 },
    { id: "el_4", name: "ServerProcedures", type: "procedure", status: "pending", sourceFile: "ServerProcedures.wdg", lines: 800, dependencies: 4, dependents: 12 },
    { id: "el_5", name: "QRY_Clientes", type: "query", status: "pending", sourceFile: "QRY_Clientes.WDR", lines: 45, dependencies: 1, dependents: 3 },
  ],
};

const mockElementCode: Record<string, string> = {
  el_1: `// PAGE_Login - WLanguage source
PROCEDURE PAGE_Login()
  EDT_Login = ""
  EDT_Senha = ""
END`,
  el_3: `// classUsuario
classUsuario is Class
  sNome is string
  sEmail is string
END`,
};

export function getMockElementCode(elementId: string): string | undefined {
  return mockElementCode[elementId];
}

// ── Conversions ───────────────────────────────────────────────────────

export const mockConversions: Record<string, Conversion[]> = {
  proj_1: [
    {
      id: "conv_1",
      projectId: "proj_1",
      name: "Login Flow",
      description: "Conversão do fluxo de login",
      status: "completed",
      elementsTotal: 2,
      elementsConverted: 2,
      tokensUsed: 45000,
      createdAt: new Date("2025-01-10"),
      updatedAt: new Date("2025-01-12"),
    },
  ],
};

export const mockConversionDetails: Record<string, Conversion & { elements?: ConversionElement[] }> = {
  conv_1: {
    id: "conv_1",
    projectId: "proj_1",
    name: "Login Flow",
    description: "Conversão do fluxo de login",
    status: "completed",
    elementsTotal: 2,
    elementsConverted: 2,
    tokensUsed: 45000,
    createdAt: new Date("2025-01-10"),
    updatedAt: new Date("2025-01-12"),
    elements: [
      {
        id: "ce_1",
        elementId: "el_1",
        elementName: "PAGE_Login",
        elementType: "page",
        status: "converted",
        originalCode: "// WLanguage original",
        convertedCode: "# Python converted",
      },
      {
        id: "ce_2",
        elementId: "el_3",
        elementName: "classUsuario",
        elementType: "class",
        status: "converted",
      },
    ],
  },
};

// ── Token Usage ───────────────────────────────────────────────────────

export const mockTokenUsage: Record<string, TokenUsageResponse> = {
  proj_1: {
    project_id: "proj_1",
    total_sessions: 5,
    total_input_tokens: 85000,
    total_output_tokens: 40000,
    total_cost_usd: 1.25,
    recent_logs: [
      {
        session_id: "sess_1",
        input_tokens: 20000,
        output_tokens: 10000,
        cost_usd: 0.30,
        model: "claude-sonnet-4-20250514",
        created_at: "2025-01-15T10:00:00Z",
      },
    ],
  },
};
