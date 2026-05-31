# db/listas.py
# Funções de listagem usadas em filtros e selects de formulários.
# Todas retornam {label: id} para facilitar o uso com st.selectbox/multiselect.

import pandas as pd
from supabase import Client
from functools import lru_cache


@lru_cache(maxsize=None)
def _cached(fn, sb):
    return fn(sb)


def mentores_map(sb: Client) -> dict[str, str]:
    """Retorna {nome: id} dos mentores ativos."""
    res = sb.table("mentores").select("id, nome").eq("ativo", True).order("nome").execute()
    return {r["nome"]: r["id"] for r in res.data}


def cursos_map(sb: Client) -> dict[str, str]:
    """Retorna {codigo: id} dos cursos."""
    res = sb.table("cursos").select("id, codigo").order("codigo").execute()
    return {r["codigo"]: r["id"] for r in res.data}


def turmas_map(sb: Client, curso_ids: list[str] = None) -> dict[str, str]:
    """Retorna {codigo: id} das turmas, opcionalmente filtradas por curso."""
    q = sb.table("turmas").select("id, codigo").order("codigo")
    if curso_ids:
        q = q.in_("curso_id", curso_ids)
    res = q.execute()
    return {r["codigo"]: r["id"] for r in res.data}


def avaliacoes_map(sb: Client, turma_id: str) -> dict[str, str]:
    """Retorna {numero: id} das avaliações de uma turma."""
    res = (
        sb.table("avaliacoes")
        .select("id, numero")
        .eq("turma_id", turma_id)
        .order("data_prevista")
        .execute()
    )
    return {r["numero"]: r["id"] for r in res.data}


def mentor_por_email(sb: Client, email: str) -> dict | None:
    """Busca o registro de mentor pelo e-mail logado."""
    res = sb.table("mentores").select("*").eq("email", email).single().execute()
    return res.data
