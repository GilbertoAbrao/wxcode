#!/bin/bash

echo "=== BACKEND STATUS ==="
curl -s http://localhost:8052/health || echo "Backend não respondeu"

echo ""
echo "=== FRONTEND STATUS ==="
curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" http://localhost:3052 || echo "Frontend não respondeu"

echo ""
echo "=== PROCESSOS ATIVOS ==="
echo "Frontend (Next.js - porta 3052):"
ps aux | grep "next dev -p 3052" | grep -v grep | awk '{print "  PID:", $2}' || echo "  Não encontrado"

echo ""
echo "Backend (porta 8052):"
lsof -ti:8052 | head -1 | xargs -I {} echo "  PID: {}" || echo "  Não encontrado"

echo ""
echo "=== URLs DE ACESSO ==="
echo "  Backend:  http://localhost:8052"
echo "  Frontend: http://localhost:3052"
