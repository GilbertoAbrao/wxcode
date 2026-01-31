/**
 * WXCODE Command Friendly Names
 *
 * Maps /wxcode:command-name to user-friendly Portuguese labels
 * for display in chat buttons.
 */

export interface WxcodeCommand {
  /** Command slug (e.g., "complete-milestone") */
  slug: string;
  /** Full command (e.g., "/wxcode:complete-milestone") */
  full: string;
  /** Friendly Portuguese label */
  label: string;
  /** Short description */
  description: string;
  /** Category for grouping */
  category: "workflow" | "planning" | "execution" | "management" | "sync" | "misc";
}

/**
 * All WXCODE commands with friendly names
 */
export const WXCODE_COMMANDS: Record<string, WxcodeCommand> = {
  // === Workflow commands ===
  "new-project": {
    slug: "new-project",
    full: "/wxcode:new-project",
    label: "Novo Projeto",
    description: "Inicializa um novo projeto com coleta de contexto",
    category: "workflow",
  },
  "new-milestone": {
    slug: "new-milestone",
    full: "/wxcode:new-milestone",
    label: "Novo Milestone",
    description: "Inicia um novo ciclo de milestone",
    category: "workflow",
  },
  "complete-milestone": {
    slug: "complete-milestone",
    full: "/wxcode:complete-milestone",
    label: "Concluir Milestone",
    description: "Arquiva milestone concluído e prepara o próximo",
    category: "workflow",
  },
  "audit-milestone": {
    slug: "audit-milestone",
    full: "/wxcode:audit-milestone",
    label: "Auditar Milestone",
    description: "Verifica conclusão do milestone antes de arquivar",
    category: "workflow",
  },
  "progress": {
    slug: "progress",
    full: "/wxcode:progress",
    label: "Ver Progresso",
    description: "Mostra progresso do projeto e próxima ação",
    category: "workflow",
  },
  "dashboard": {
    slug: "dashboard",
    full: "/wxcode:dashboard",
    label: "Gerar Dashboard",
    description: "Gera JSON de progresso e notifica watchers",
    category: "workflow",
  },

  // === Planning commands ===
  "plan-phase": {
    slug: "plan-phase",
    full: "/wxcode:plan-phase",
    label: "Planejar Fase",
    description: "Cria plano de execução detalhado (PLAN.md)",
    category: "planning",
  },
  "research-phase": {
    slug: "research-phase",
    full: "/wxcode:research-phase",
    label: "Pesquisar Fase",
    description: "Pesquisa como implementar uma fase",
    category: "planning",
  },
  "discuss-phase": {
    slug: "discuss-phase",
    full: "/wxcode:discuss-phase",
    label: "Discutir Fase",
    description: "Coleta contexto através de perguntas antes de planejar",
    category: "planning",
  },
  "discuss": {
    slug: "discuss",
    full: "/wxcode:discuss",
    label: "Discutir Mudança",
    description: "Explora e planeja novas features ou mudanças",
    category: "planning",
  },
  "list-phase-assumptions": {
    slug: "list-phase-assumptions",
    full: "/wxcode:list-phase-assumptions",
    label: "Listar Premissas",
    description: "Mostra premissas do Claude sobre a abordagem da fase",
    category: "planning",
  },
  "plan-milestone-gaps": {
    slug: "plan-milestone-gaps",
    full: "/wxcode:plan-milestone-gaps",
    label: "Planejar Gaps",
    description: "Cria fases para fechar gaps identificados na auditoria",
    category: "planning",
  },

  // === Execution commands ===
  "execute-phase": {
    slug: "execute-phase",
    full: "/wxcode:execute-phase",
    label: "Executar Fase",
    description: "Executa todos os planos da fase com paralelização",
    category: "execution",
  },
  "verify-work": {
    slug: "verify-work",
    full: "/wxcode:verify-work",
    label: "Verificar Trabalho",
    description: "Valida features através de UAT conversacional",
    category: "execution",
  },
  "quick": {
    slug: "quick",
    full: "/wxcode:quick",
    label: "Tarefa Rápida",
    description: "Executa tarefa rápida com garantias WXCODE",
    category: "execution",
  },
  "debug": {
    slug: "debug",
    full: "/wxcode:debug",
    label: "Debug",
    description: "Debugging sistemático com estado persistente",
    category: "execution",
  },

  // === Management commands ===
  "add-phase": {
    slug: "add-phase",
    full: "/wxcode:add-phase",
    label: "Adicionar Fase",
    description: "Adiciona fase ao final do milestone atual",
    category: "management",
  },
  "insert-phase": {
    slug: "insert-phase",
    full: "/wxcode:insert-phase",
    label: "Inserir Fase",
    description: "Insere trabalho urgente como fase decimal",
    category: "management",
  },
  "remove-phase": {
    slug: "remove-phase",
    full: "/wxcode:remove-phase",
    label: "Remover Fase",
    description: "Remove fase futura e renumera as seguintes",
    category: "management",
  },
  "add-todo": {
    slug: "add-todo",
    full: "/wxcode:add-todo",
    label: "Adicionar Todo",
    description: "Captura ideia ou tarefa como todo",
    category: "management",
  },
  "check-todos": {
    slug: "check-todos",
    full: "/wxcode:check-todos",
    label: "Ver Todos",
    description: "Lista todos pendentes e seleciona um para trabalhar",
    category: "management",
  },
  "pause-work": {
    slug: "pause-work",
    full: "/wxcode:pause-work",
    label: "Pausar Trabalho",
    description: "Cria handoff de contexto ao pausar trabalho",
    category: "management",
  },
  "resume-work": {
    slug: "resume-work",
    full: "/wxcode:resume-work",
    label: "Retomar Trabalho",
    description: "Retoma trabalho com restauração completa de contexto",
    category: "management",
  },
  "map-codebase": {
    slug: "map-codebase",
    full: "/wxcode:map-codebase",
    label: "Mapear Código",
    description: "Analisa codebase com agentes paralelos",
    category: "management",
  },

  // === Sync commands ===
  "init": {
    slug: "init",
    full: "/wxcode:init",
    label: "Inicializar Fork",
    description: "Inicializa gerenciamento de fork WXCODE",
    category: "sync",
  },
  "sync": {
    slug: "sync",
    full: "/wxcode:sync",
    label: "Sincronizar",
    description: "Sincroniza fork com repositório upstream",
    category: "sync",
  },
  "status": {
    slug: "status",
    full: "/wxcode:status",
    label: "Ver Status",
    description: "Mostra estado atual e atualizações disponíveis",
    category: "sync",
  },
  "update": {
    slug: "update",
    full: "/wxcode:update",
    label: "Atualizar WXCODE",
    description: "Atualiza para última versão com changelog",
    category: "sync",
  },
  "diff": {
    slug: "diff",
    full: "/wxcode:diff",
    label: "Ver Diferenças",
    description: "Compara arquivo local com equivalente upstream",
    category: "sync",
  },
  "rollback": {
    slug: "rollback",
    full: "/wxcode:rollback",
    label: "Reverter Sync",
    description: "Reverte a última operação de sync",
    category: "sync",
  },
  "history": {
    slug: "history",
    full: "/wxcode:history",
    label: "Ver Histórico",
    description: "Visualiza histórico de sync e decisões",
    category: "sync",
  },
  "override": {
    slug: "override",
    full: "/wxcode:override",
    label: "Ignorar Arquivo",
    description: "Marca arquivo para ignorar mudanças upstream",
    category: "sync",
  },
  "customize": {
    slug: "customize",
    full: "/wxcode:customize",
    label: "Customizar",
    description: "Customiza comando ou agente específico",
    category: "sync",
  },

  // === Misc commands ===
  "help": {
    slug: "help",
    full: "/wxcode:help",
    label: "Ajuda",
    description: "Mostra comandos WXCODE disponíveis",
    category: "misc",
  },
  "settings": {
    slug: "settings",
    full: "/wxcode:settings",
    label: "Configurações",
    description: "Configura toggles e perfil de modelo",
    category: "misc",
  },
  "set-profile": {
    slug: "set-profile",
    full: "/wxcode:set-profile",
    label: "Definir Perfil",
    description: "Troca perfil de modelo (quality/balanced/budget)",
    category: "misc",
  },
  "join-discord": {
    slug: "join-discord",
    full: "/wxcode:join-discord",
    label: "Entrar no Discord",
    description: "Entra na comunidade WXCODE no Discord",
    category: "misc",
  },
};

/**
 * Get friendly label for a /wxcode:command string
 *
 * @param command - Full command string (e.g., "/wxcode:plan-phase 1")
 * @returns Friendly label or the original command if not found
 */
export function getCommandLabel(command: string): string {
  // Extract command slug from "/wxcode:command-name args"
  const match = command.match(/^\/wxcode:([a-z-]+)/);
  if (!match) return command;

  const slug = match[1];
  const cmd = WXCODE_COMMANDS[slug];

  if (!cmd) return command;

  // If command has arguments, append them to the label
  const args = command.slice(match[0].length).trim();
  if (args) {
    return `${cmd.label} ${args}`;
  }

  return cmd.label;
}

/**
 * Get command info by slug
 */
export function getCommand(slug: string): WxcodeCommand | undefined {
  return WXCODE_COMMANDS[slug];
}

/**
 * Get all commands grouped by category
 */
export function getCommandsByCategory(): Record<string, WxcodeCommand[]> {
  const grouped: Record<string, WxcodeCommand[]> = {};

  for (const cmd of Object.values(WXCODE_COMMANDS)) {
    if (!grouped[cmd.category]) {
      grouped[cmd.category] = [];
    }
    grouped[cmd.category].push(cmd);
  }

  return grouped;
}
