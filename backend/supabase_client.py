"""
Cliente Supabase — inicialização e acesso global.

Fornece uma instância única do cliente Supabase configurada
com as credenciais do projeto.
"""

from __future__ import annotations

import logging
from typing import Any

from supabase import Client, create_client
from supabase.lib.client_options import ClientOptions

from config import config

logger = logging.getLogger(__name__)

_client: Client | None = None


def init_supabase() -> Client | None:
    """
    Inicializa o cliente Supabase.

    Retorna None se as credenciais não estiverem configuradas
    (útil para desenvolvimento sem Supabase).
    """
    global _client

    if not config.supabase_url or not config.supabase_anon_key:
        logger.warning(
            "Supabase não configurado: SUPABASE_URL e SUPABASE_ANON_KEY "
            "devem estar definidos no .env"
        )
        return None

    try:
        _client = create_client(
            supabase_url=config.supabase_url,
            supabase_key=config.supabase_anon_key,
            options=ClientOptions(
                postgrest_client_timeout=10,
                storage_client_timeout=10,
                schema="public",
            ),
        )
        logger.info("Cliente Supabase inicializado com sucesso")
        return _client
    except Exception as exc:
        logger.error("Falha ao inicializar cliente Supabase: %s", exc)
        return None


def get_supabase() -> Client | None:
    """Retorna a instância global do cliente Supabase."""
    return _client


def get_user_email(user_id: str) -> str | None:
    """
    Busca o email de um usuário pelo ID.

    Requer service_role key — não disponível no client anônimo.
    Retorna None se não for possível buscar.
    """
    client = get_supabase()
    if not client:
        return None

    try:
        # Nota: em produção, o user_id vem do JWT e o email já está no payload.
        # Esta função é para casos excepcionais (admin, logging).
        response = client.table("auth.users").select("email").eq("id", user_id).execute()
        if response.data:
            return response.data[0].get("email")
    except Exception as exc:
        logger.debug("Não foi possível buscar email do usuário %s: %s", user_id, exc)

    return None
