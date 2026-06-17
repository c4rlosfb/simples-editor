#!/bin/bash
#=============================================================================
# Sandbox Security Audit - Simples Editor
#
# Testa as tres principais superficies de ataque do sandbox Docker:
#   1. Escrita em / (read-only filesystem)
#   2. Fork bomb (pids_limit)
#   3. Acesso a rede (network_mode=none)
#
# Uso: bash scripts/test-sandbox.sh
#=============================================================================

set -euo pipefail

SANDBOX_IMAGE="${1:-simples-runner:latest}"
PASS=0
FAIL=0

green() { echo -e "\033[32m[PASS]\033[0m $1"; ((PASS++)); }
red()   { echo -e "\033[31m[FAIL]\033[0m $1"; ((FAIL++)); }

echo "=================================================="
echo " Sandbox Security Audit"
echo " Image: $SANDBOX_IMAGE"
echo "=================================================="
echo ""

# ------------------------------------------------------------------
# Test 1: Escrita em /
# ------------------------------------------------------------------
echo "--- Test 1: Escrita em / (read-only filesystem) ---"
if docker run --rm --read-only "$SANDBOX_IMAGE" sh -c "touch /test.txt" 2>/dev/null; then
    red "Container conseguiu escrever em / (read-only falhou)"
else
    green "Container NAO conseguiu escrever em / (read-only OK)"
fi

if docker run --rm --read-only "$SANDBOX_IMAGE" sh -c "touch /tmp/test.txt" 2>/dev/null; then
    green "Container conseguiu escrever em /tmp (tmpfs OK)"
else
    red "Container NAO conseguiu escrever em /tmp (tmpfs ausente)"
fi

# ------------------------------------------------------------------
# Test 2: Fork bomb (pids_limit)
# ------------------------------------------------------------------
echo ""
echo "--- Test 2: Fork bomb (pids_limit) ---"
if docker run --rm --pids-limit=64 "$SANDBOX_IMAGE" sh -c "
    bomb() { bomb & }; bomb
" 2>/dev/null &
then
    BOMB_PID=$!
    sleep 3
    if kill -0 $BOMB_PID 2>/dev/null; then
        red "Fork bomb nao foi contida (pids_limit pode estar muito alto)"
        kill $BOMB_PID 2>/dev/null || true
    else
        green "Fork bomb foi contida pelo pids_limit (OK)"
    fi
else
    green "Fork bomb foi rejeitada (OK)"
fi

# ------------------------------------------------------------------
# Test 3: Acesso a rede
# ------------------------------------------------------------------
echo ""
echo "--- Test 3: Acesso a rede (network_mode=none) ---"
if docker run --rm --network=none "$SANDBOX_IMAGE" sh -c "ping -c 1 8.8.8.8" 2>/dev/null; then
    red "Container conseguiu acessar a rede (network_mode=none falhou)"
else
    green "Container NAO conseguiu acessar a rede (network_mode=none OK)"
fi

if docker run --rm --network=none "$SANDBOX_IMAGE" sh -c "wget -q http://google.com -O /dev/null" 2>/dev/null; then
    red "Container conseguiu fazer HTTP request (network_mode=none falhou)"
else
    green "Container NAO conseguiu fazer HTTP request (network_mode=none OK)"
fi

# ------------------------------------------------------------------
# Resumo
# ------------------------------------------------------------------
echo ""
echo "=================================================="
echo " Resultado: $PASS passaram, $FAIL falharam"
echo "=================================================="

if [ "$FAIL" -gt 0 ]; then
    exit 1
fi
exit 0
