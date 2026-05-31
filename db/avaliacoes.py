# db/avaliacoes.py
import pandas as pd
from datetime import date
from supabase import Client


_SELECT = """
    id, numero, tipo, local, data_prevista, data_realizada,
    status, resultado_medio, ciclo, link_forms, observacoes,
    mentores!responsavel_id ( id, nome ),
    turmas (
        id, codigo, turno,
        cursos ( id, codigo, nome_completo )
    )
"""


def _flatten(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    df = df.copy()
    df["responsavel"]    = df["mentores"].apply(lambda x: x["nome"]   if x else "—")
    df["responsavel_id"] = df["mentores"].apply(lambda x: x["id"]     if x else None)
    df["turma"]          = df["turmas"].apply(lambda x: x["codigo"]   if x else "—")
    df["turma_id_fk"]    = df["turmas"].apply(lambda x: x["id"]       if x else None)
    df["curso"]          = df["turmas"].apply(
        lambda x: x["cursos"]["codigo"] if x and x.get("cursos") else "—"
    )
    df["resultado_%"] = df["resultado_medio"].apply(
        lambda v: f"{v*100:.1f}%" if v is not None else "—"
    )
    return df.drop(columns=["mentores", "turmas"])


def listar_avaliacoes(
    sb: Client,
    turma_id:    str       = None,
    responsavel_id: str    = None,
    status:      list[str] = None,
    data_ini:    date      = None,
    data_fim:    date      = None,
) -> pd.DataFrame:
    q = sb.table("avaliacoes").select(_SELECT).order("data_prevista")

    if turma_id:
        q = q.eq("turma_id", turma_id)
    if responsavel_id:
        q = q.eq("responsavel_id", responsavel_id)
    if status:
        q = q.in_("status", status)
    if data_ini:
        q = q.gte("data_prevista", str(data_ini))
    if data_fim:
        q = q.lte("data_prevista", str(data_fim))

    res = q.execute()
    return _flatten(pd.DataFrame(res.data))


def criar_avaliacao(sb: Client, dados: dict) -> dict:
    res = sb.table("avaliacoes").insert(dados).execute()
    return res.data[0] if res.data else {}


def atualizar_avaliacao(sb: Client, aval_id: str, dados: dict) -> dict:
    res = sb.table("avaliacoes").update(dados).eq("id", aval_id).execute()
    return res.data[0] if res.data else {}


def excluir_avaliacao(sb: Client, aval_id: str) -> None:
    sb.table("avaliacoes").delete().eq("id", aval_id).execute()
