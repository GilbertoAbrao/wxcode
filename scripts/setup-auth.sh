#!/bin/bash
#
# setup-auth.sh - Configura autenticação Claude Code em volume Docker
#
# Este script cria um volume Docker para armazenar credenciais OAuth
# do Claude Code e executa o processo de login interativamente.
#
# Uso:
#   ./scripts/setup-auth.sh
#
# Após a execução, o volume 'claude-credentials' estará disponível
# para ser montado em containers que precisam usar Claude Code.

set -e

VOLUME_NAME="claude-credentials"
CONTAINER_NAME="claude-setup"
IMAGE="node:22-slim"

echo "=== WXCODE: Setup de Autenticação Claude Code ==="
echo ""

# Verifica se Docker está disponível
if ! command -v docker &> /dev/null; then
    echo "❌ Docker não encontrado. Por favor, instale o Docker primeiro."
    exit 1
fi

# Verifica se volume já existe
if docker volume inspect "$VOLUME_NAME" &> /dev/null; then
    echo "⚠️  Volume '$VOLUME_NAME' já existe."
    read -p "Deseja recriar? Isso apagará as credenciais existentes. (y/N) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🗑️  Removendo volume existente..."
        docker volume rm "$VOLUME_NAME"
    else
        echo "ℹ️  Mantendo volume existente."
        echo ""
        echo "Para testar se as credenciais funcionam, execute:"
        echo "  docker run --rm -v $VOLUME_NAME:/home/node/.claude $IMAGE npx -y @anthropic-ai/claude-code --version"
        exit 0
    fi
fi

# Cria volume
echo "📦 Criando volume Docker '$VOLUME_NAME'..."
docker volume create "$VOLUME_NAME"

# Executa login interativo
echo ""
echo "🔐 Iniciando processo de login do Claude Code..."
echo "   Você será redirecionado para o navegador para autenticar."
echo ""

docker run -it --rm \
    --name "$CONTAINER_NAME" \
    -v "$VOLUME_NAME":/home/node/.claude \
    -e HOME=/home/node \
    "$IMAGE" \
    bash -c "
        echo '📥 Instalando Claude Code...'
        npm install -g @anthropic-ai/claude-code --quiet

        echo ''
        echo '🔑 Executando login...'
        echo '   Siga as instruções no navegador.'
        echo ''

        claude login

        echo ''
        if [ -f /home/node/.claude/.credentials.json ]; then
            echo '✅ Login realizado com sucesso!'
            echo ''
            echo 'Credenciais salvas no volume docker: $VOLUME_NAME'
        else
            echo '❌ Falha no login. Por favor, tente novamente.'
            exit 1
        fi
    "

echo ""
echo "=== Setup Concluído ==="
echo ""
echo "O volume '$VOLUME_NAME' agora contém as credenciais OAuth."
echo ""
echo "Para usar em um container, monte o volume:"
echo "  docker run -v $VOLUME_NAME:/home/node/.claude:ro ..."
echo ""
echo "Para usar no docker-compose.yml, adicione:"
echo "  volumes:"
echo "    - claude-credentials:/home/node/.claude:ro"
echo ""
echo "⚠️  IMPORTANTE: NÃO defina ANTHROPIC_API_KEY nos containers,"
echo "   caso contrário a API Key será usada em vez da assinatura."
