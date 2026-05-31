# db/acoes.py
import pandas as pd
from datetime import date
from supabase import Client


_SELECT = """
    id, tipo, o_que, porque, onde, como,
    quando_previsto, data_realizacao,
    status, observacoes, encaminhamentos,
    criado_em, atualizado_em,
    mentores!quem_id ( id, nome ),
    cursos            ( id, codigo, nome_completo ),
    turmas            ( id, codigo, turno )
"""


def _flatten(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    df = df.copy()
    df["mentor_id"]   = df["mentores"].apply(lambda x: x["id"]   if x else None)
    df["mentor"]      = df["mentores"].apply(lambda x: x["nome"] if x else "—")
    df["curso_id"]    = df["cursos"].apply(lambda x: x["id"]     if x else None)
    df["curso"]       = df["cursos"].apply(lambda x: x["codigo"] if x else "—")
    df["turma_id_fk"] = df["turmas"].apply(lambda x: x["id"]     if x else None)
    df["turma"]       = df["turmas"].apply(lambda x: x["codigo"] if x else "—")
    return df.drop(columns=["mentores", "cursos", "turmas"])


def listar_acoes(
    sb: Client,
    mentor_id:   str        = None,
    curso_id:    str        = None,
    turma_id:    str        = None,
    status:      list[str]  = None,
    tipo:        list[str]  = None,
    data_ini:    date       = None,
    data_fim:    date       = None,
) -> pd.DataFrame:
    q = sb.table("acoes").select(_SELECT).order("quando_previsto", desc=False)

    if mentor_id:
        q = q.eq("quem_id", mentor_id)
    if curso_id:
        q = q.eq("curso_id", curso_id)
    if turma_id:
        q = q.eq("turma_id", turma_id)
    if status:
        q = q.in_("status", status)
    if tipo:
        q = q.in_("tipo", tipo)
    if data_ini:
        q = q.gte("quando_previsto", str(data_ini))
    if data_fim:
        q = q.lte("quando_previsto", str(data_fim))

    res = q.execute()
    return _flatten(pd.DataFrame(res.data))


def buscar_acao(sb: Client, acao_id: str) -> dict:
    res = sb.table("acoes").select(_SELECT).eq("id", acao_id).single().execute()
    return res.data or {}


def criar_acao(sb: Client, dados: dict) -> dict:
    res = sb.table("acoes").insert(dados).execute()
    return res.data[0] if res.data else {}


def atualizar_acao(sb: Client, acao_id: str, dados: dict) -> dict:
    res = sb.table("acoes").update(dados).eq("id", acao_id).execute()
    return res.data[0] if res.data else {}


def atualizar_status(sb: Client, acao_id: str, novo_status: str) -> None:
    """
    Atualiza apenas o status.
    O trigger no banco grava automaticamente em historico_acoes.
    """
    payload = {"status": novo_status}
    if novo_status == "REALIZADO":
        payload["data_realizacao"] = str(date.today())
    sb.table("acoes").update(payload).eq("id", acao_id).execute()


def excluir_acao(sb: Client, acao_id: str) -> None:
    sb.table("acoes").delete().eq("id", acao_id).execute()


def acoes_atrasadas(sb: Client) -> pd.DataFrame:
    """Retorna ações vencidas que ainda não estão marcadas como atrasadas."""
    hoje = str(date.today())
    res = (
        sb.table("acoes")
        .select("id, status, quando_previsto, quem_id")
        .lt("quando_previsto", hoje)
        .not_.in_("status", ["REALIZADO", "ATRASADO", "NÃO REALIZADO"])
        .execute()
    )
    return pd.DataFrame(res.data)


def marcar_atrasadas_automatico(sb: Client) -> int:
    """
    Marca como ATRASADO todas as ações vencidas.
    Chame no início de cada página para manter o banco atualizado.
    Retorna o número de ações atualizadas.
    """
    df = acoes_atrasadas(sb)
    if df.empty:
        return 0
    ids = df["id"].tolist()
    sb.table("acoes").update({"status": "ATRASADO"}).in_("id", ids).execute()
    return len(ids)
