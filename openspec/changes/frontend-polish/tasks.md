# Tasks: frontend-polish

## Task 1: Instalar dependências

**Steps:**
1. `npm install framer-motion`
2. `npm install @fontsource-variable/jetbrains-mono`

**Acceptance Criteria:**
- [x] framer-motion instalado
- [x] JetBrains Mono instalado

---

## Task 2: Configurar fontes

**File:** `frontend/src/app/layout.tsx`

**Steps:**
1. Importar Geist Sans e Geist Mono do next/font
2. Importar JetBrains Mono
3. Aplicar variáveis CSS de fonte

**Acceptance Criteria:**
- [x] Geist Sans como fonte padrão
- [x] JetBrains Mono para código
- [x] CSS variables --font-sans, --font-mono

---

## Task 3: Criar design tokens

**File:** `frontend/src/styles/tokens.css`

**Steps:**
1. Definir paleta Obsidian (950-100)
2. Definir accent colors com glow variants
3. Definir spacing, radius, shadows

**Acceptance Criteria:**
- [x] CSS variables para todas as cores
- [x] Glow variants para cada accent
- [x] Tokens de spacing/radius

---

## Task 4: Atualizar globals.css

**File:** `frontend/src/app/globals.css`

**Steps:**
1. Importar tokens.css
2. Aplicar cores base no :root
3. Adicionar grain texture overlay
4. Definir transições globais

**Acceptance Criteria:**
- [x] Background usa obsidian-950
- [x] Grain overlay sutil
- [x] Transições suaves globais

---

## Task 5: Criar animation variants

**File:** `frontend/src/lib/animations.ts`

**Steps:**
1. Criar variants para fadeIn, slideIn
2. Criar variants para stagger children
3. Criar variants para glow pulse

**Acceptance Criteria:**
- [x] fadeIn, fadeInUp, fadeInDown
- [x] staggerContainer, staggerItem
- [x] glowPulse variant

---

## Task 6: Criar LoadingSkeleton component

**File:** `frontend/src/components/ui/LoadingSkeleton.tsx`

**Steps:**
1. Skeleton com shimmer animation
2. Variants: text, card, avatar, list
3. Props para width, height, className

**Acceptance Criteria:**
- [x] Shimmer gradient animado
- [x] Múltiplas variants
- [x] Customizável via props

---

## Task 7: Criar EmptyState component

**File:** `frontend/src/components/ui/EmptyState.tsx`

**Steps:**
1. Layout centered com ícone
2. Título, descrição, action button
3. Animação de entrada

**Acceptance Criteria:**
- [x] Ícone customizável
- [x] Action button opcional
- [x] Fade in animation

---

## Task 8: Criar ErrorState component

**File:** `frontend/src/components/ui/ErrorState.tsx`

**Steps:**
1. Layout com ícone de erro
2. Mensagem de erro, retry button
3. Estilo rose/red accent

**Acceptance Criteria:**
- [x] Ícone AlertCircle
- [x] Retry callback
- [x] Cor accent-rose

---

## Task 9: Criar GlowButton component

**File:** `frontend/src/components/ui/GlowButton.tsx`

**Steps:**
1. Button com glow effect no hover
2. Variants: primary, success, danger
3. Loading state com spinner

**Acceptance Criteria:**
- [x] Glow sutil no hover
- [x] 3 variants de cor
- [x] Loading spinner

---

## Task 10: Criar GlowInput component

**File:** `frontend/src/components/ui/GlowInput.tsx`

**Steps:**
1. Input com glow ring no focus
2. Suporte a ícone prefix
3. Error state styling

**Acceptance Criteria:**
- [x] Glow ring animado no focus
- [x] Ícone prefix opcional
- [x] Error border + message

---

## Task 11: Criar AnimatedList component

**File:** `frontend/src/components/ui/AnimatedList.tsx`

**Steps:**
1. Wrapper que anima children com stagger
2. Usa framer-motion AnimatePresence
3. Props para delay e duration

**Acceptance Criteria:**
- [x] Stagger animation nos items
- [x] AnimatePresence para exit
- [x] Customizável

---

## Task 12: Criar index exports UI

**File:** `frontend/src/components/ui/index.ts`

**Steps:**
1. Exportar todos componentes ui/
2. Re-exportar animation variants

**Acceptance Criteria:**
- [x] Todos componentes exportados
- [x] Animations re-exportados

---

## Task 13: Refinar ProjectCard

**File:** `frontend/src/components/project/ProjectCard.tsx`

**Steps:**
1. Adicionar hover glow effect
2. Animação de entrada
3. Usar novas cores

**Acceptance Criteria:**
- [x] Glow no hover
- [x] Scale sutil
- [x] Cores Obsidian

---

## Task 14: Refinar ElementTree

**File:** `frontend/src/components/project/ElementTree.tsx`

**Steps:**
1. Stagger animation nos items
2. Hover states refinados
3. Selection glow

**Acceptance Criteria:**
- [x] Items animam ao carregar
- [x] Hover suave
- [x] Selected item com glow

---

## Task 15: Validar build e commit

**Steps:**
1. `npm run build`
2. Verificar sem erros
3. Commit changes

**Acceptance Criteria:**
- [x] Build passa
- [x] Sem warnings críticos
- [x] Commit feito

---

## Dependencies

```
Task 1 → Tasks 2-4 (setup base)
Tasks 2-4 → Task 5 (animations)
Task 5 → Tasks 6-11 (components)
Tasks 6-11 → Task 12 (exports)
Task 12 → Tasks 13-14 (refinements)
Tasks 13-14 → Task 15 (validation)
```

## Validation Commands

```bash
cd frontend && npm run build
cd frontend && npm run dev
# Verificar visual em http://localhost:3000
```
