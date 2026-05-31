# db/resultados.py
import pandas as pd
from supabase import Client


def listar_resultados(sb: Client, avaliacao_id: str) -> pd.DataFrame:
    res = (
        sb.table("resultados_alunos")
        .select("id, nome_aluno, pontuacao, escala, dificuldades, intervencao")
        .eq("avaliacao_id", avaliacao_id)
        .order("nome_aluno")
        .execute()
    )
    return pd.DataFrame(res.data)


def upsert_resultados(sb: Client, registros: list[dict]) -> None:
    """
    Insere ou atualiza resultados em lote.
    Cada dict deve ter: avaliacao_id, nome_aluno, pontuacao, escala.
    """
    if not registros:
        return
    # Lotes de 50 para respeitar o limite do Supabase free
    for i in range(0, len(registros), 50):
        sb.table("resultados_alunos").upsert(
            registros[i:i+50],
            on_conflict="avaliacao_id,nome_aluno"
        ).execute()


def excluir_resultado(sb: Client, resultado_id: str) -> None:
    sb.table("resultados_alunos").delete().eq("id", resultado_id).execute()


def distribuicao_escala(sb: Client, avaliacao_id: str) -> dict:
    """Retorna contagem por nível: {'AV': 5, 'AD': 10, 'B': 3, 'AB': 2}"""
    df = listar_resultados(sb, avaliacao_id)
    if df.empty:
        return {}
    return df["escala"].value_counts().to_dict()
