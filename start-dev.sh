#!/bin/bash
# Script para iniciar backend + frontend em desenvolvimento

set -e

# Cores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  WXCODE Development Server${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Verifica se está no diretório correto
if [ ! -f "setup.py" ] && [ ! -f "pyproject.toml" ]; then
    echo -e "${YELLOW}❌ Execute este script do diretório raiz do projeto${NC}"
    exit 1
fi

# Verifica dependências
if ! command -v python &> /dev/null; then
    echo -e "${YELLOW}❌ Python não encontrado${NC}"
    exit 1
fi

if ! command -v npm &> /dev/null; then
    echo -e "${YELLOW}❌ npm não encontrado${NC}"
    exit 1
fi

# Mata processos nas portas usadas
echo -e "${YELLOW}🧹 Liberando portas 8052 e 3052...${NC}"
lsof -ti :8052 | xargs kill -9 2>/dev/null || true
lsof -ti :3052 | xargs kill -9 2>/dev/null || true
sleep 2

# Função para cleanup
cleanup() {
    echo ""
    echo -e "${BLUE}🛑 Encerrando servidores...${NC}"
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    exit 0
}

trap cleanup SIGINT SIGTERM

# Inicia backend
echo -e "${GREEN}🚀 Iniciando backend (porta 8052)...${NC}"
DEBUG=false PYTHONDONTWRITEBYTECODE=1 python -m uvicorn wxcode.main:app --host 0.0.0.0 --port 8052 > /tmp/wxcode-backend.log 2>&1 &
BACKEND_PID=$!
echo "   PID: $BACKEND_PID"
sleep 3

# Verifica se backend iniciou
if ! curl -s http://localhost:8052/health > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Backend pode estar demorando para iniciar...${NC}"
fi

# Inicia frontend
echo -e "${GREEN}🎨 Iniciando frontend (porta 3052)...${NC}"
cd frontend
npm run dev > /tmp/wxcode-frontend.log 2>&1 &
FRONTEND_PID=$!
echo "   PID: $FRONTEND_PID"
cd ..
sleep 5

echo ""
echo -e "${GREEN}✓ Servidores iniciados!${NC}"
echo ""
echo -e "  ${BLUE}Backend:${NC}  http://localhost:8052"
echo -e "  ${BLUE}Frontend:${NC} http://localhost:3052"
echo ""
echo -e "  ${BLUE}Logs:${NC}"
echo -e "    Backend:  /tmp/wxcode-backend.log"
echo -e "    Frontend: /tmp/wxcode-frontend.log"
echo ""
echo -e "Pressione ${GREEN}Ctrl+C${NC} para encerrar"
echo ""

# Aguarda indefinidamente
wait
