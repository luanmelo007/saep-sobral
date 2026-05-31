# db/relatorios.py
import pandas as pd
from datetime import date, timedelta
from supabase import Client


# ── Períodos pré-definidos ────────────────────────────────────────────────────

def periodos_trimestrais(ano: int = None) -> dict[str, tuple]:
    if ano is None:
        ano = date.today().year
    hoje = date.today()
    return {
        f"T1 {ano} — Jan a Mar":      (date(ano, 1, 1),  date(ano, 3, 31)),
        f"T2 {ano} — Abr a Jun":      (date(ano, 4, 1),  date(ano, 6, 30)),
        f"T3 {ano} — Jul a Set":      (date(ano, 7, 1),  date(ano, 9, 30)),
        f"T4 {ano} — Out a Dez":      (date(ano, 10, 1), date(ano, 12, 31)),
        f"Ciclo {ano}.1 — Jan a Jun": (date(ano, 1, 1),  date(ano, 6, 30)),
        f"Ciclo {ano}.2 — Jul a Dez": (date(ano, 7, 1),  date(ano, 12, 31)),
        "Últimos 30 dias":            (hoje - timedelta(days=30), hoje),
        "Últimos 90 dias":            (hoje - timedelta(days=90), hoje),
        "Este mês":                   (hoje.replace(day=1), hoje),
        "Personalizado":              (None, None),
    }


# ── Queries de relatório ──────────────────────────────────────────────────────

def relatorio_acoes(
    sb: Client,
    data_ini:   date,
    data_fim:   date,
    mentor_ids: list[str] = None,
    curso_ids:  list[str] = None,
    turma_ids:  list[str] = None,
    status:     list[str] = None,
    tipo:       list[str] = None,
) -> pd.DataFrame:
    q = (
        sb.table("acoes")
        .select("""
            id, tipo, o_que, porque, onde, como,
            quando_previsto, data_realizacao, status, observacoes,
            mentores!quem_id ( nome ),
            cursos            ( codigo ),
            turmas            ( codigo, turno )
        """)
        .gte("quando_previsto", str(data_ini))
        .lte("quando_previsto", str(data_fim))
        .order("quando_previsto")
    )
    if mentor_ids: q = q.in_("quem_id",   mentor_ids)
    if curso_ids:  q = q.in_("curso_id",  curso_ids)
    if turma_ids:  q = q.in_("turma_id",  turma_ids)
    if status:     q = q.in_("status",    status)
    if tipo:       q = q.in_("tipo",      tipo)

    df = pd.DataFrame(q.execute().data)
    if df.empty:
        return df

    df["Mentor"] = df["mentores"].apply(lambda x: x["nome"]   if x else "—")
    df["Curso"]  = df["cursos"].apply(lambda x:   x["codigo"] if x else "—")
    df["Turma"]  = df["turmas"].apply(lambda x:   x["codigo"] if x else "—")

    return df.rename(columns={
        "quando_previsto": "Previsto",
        "data_realizacao": "Realizado em",
        "status":          "Status",
        "tipo":            "Tipo",
        "o_que":           "Ação",
        "onde":            "Local",
        "observacoes":     "Observações",
    })[[
        "Previsto", "Realizado em", "Status", "Tipo",
        "Mentor", "Curso", "Turma", "Ação", "Local", "Observações",
    ]]


def relatorio_avaliacoes(
    sb: Client,
    data_ini:   date,
    data_fim:   date,
    mentor_ids: list[str] = None,
    turma_ids:  list[str] = None,
    status:     list[str] = None,
) -> pd.DataFrame:
    q = (
        sb.table("avaliacoes")
        .select("""
            id, numero, tipo, local, data_prevista, data_realizada,
            status, resultado_medio, observacoes,
            mentores!responsavel_id ( nome ),
            turmas ( codigo, cursos ( codigo ) )
        """)
        .gte("data_prevista", str(data_ini))
        .lte("data_prevista", str(data_fim))
        .order("data_prevista")
    )
    if mentor_ids: q = q.in_("responsavel_id", mentor_ids)
    if turma_ids:  q = q.in_("turma_id",       turma_ids)
    if status:     q = q.in_("status",          status)

    df = pd.DataFrame(q.execute().data)
    if df.empty:
        return df

    df["Responsável"] = df["mentores"].apply(lambda x: x["nome"] if x else "—")
    df["Turma"]       = df["turmas"].apply(lambda x:   x["codigo"] if x else "—")
    df["Curso"]       = df["turmas"].apply(
        lambda x: x["cursos"]["codigo"] if x and x.get("cursos") else "—"
    )
    df["Resultado %"] = df["resultado_medio"].apply(
        lambda v: f"{v*100:.1f}%" if v is not None else "—"
    )

    return df.rename(columns={
        "data_prevista":  "Previsto",
        "data_realizada": "Realizado em",
        "status":         "Status",
        "numero":         "Nº Avaliação",
        "tipo":           "Tipo",
        "local":          "Local",
        "observacoes":    "Observações",
    })[[
        "Previsto", "Realizado em", "Status", "Curso", "Turma",
        "Nº Avaliação", "Tipo", "Responsável", "Local", "Resultado %", "Observações",
    ]]


def relatorio_resultados(
    sb: Client,
    data_ini:  date,
    data_fim:  date,
    turma_ids: list[str] = None,
    escalas:   list[str] = None,
) -> pd.DataFrame:
    q = sb.table("resultados_alunos").select("""
        nome_aluno, pontuacao, escala, dificuldades, intervencao,
        avaliacoes (
            numero, data_prevista,
            turmas ( codigo, cursos ( codigo ) )
        )
    """)
    if escalas: q = q.in_("escala", escalas)

    df = pd.DataFrame(q.execute().data)
    if df.empty:
        return df

    df["Avaliação"] = df["avaliacoes"].apply(lambda x: x["numero"]        if x else "—")
    df["Data"]      = df["avaliacoes"].apply(lambda x: x["data_prevista"] if x else None)
    df["Turma"]     = df["avaliacoes"].apply(
        lambda x: x["turmas"]["codigo"] if x and x.get("turmas") else "—"
    )
    df["Curso"]     = df["avaliacoes"].apply(
        lambda x: x["turmas"]["cursos"]["codigo"]
        if x and x.get("turmas") and x["turmas"].get("cursos") else "—"
    )

    if data_ini: df = df[df["Data"] >= str(data_ini)]
    if data_fim: df = df[df["Data"] <= str(data_fim)]

    return df.rename(columns={
        "nome_aluno":  "Aluno",
        "pontuacao":   "Pontuação",
        "escala":      "Nível",
        "dificuldades":"Dificuldades",
        "intervencao": "Intervenção",
    })[["Data","Curso","Turma","Avaliação","Aluno","Pontuação","Nível","Dificuldades","Intervenção"]]


# ── Métricas de resumo ────────────────────────────────────────────────────────

def metricas_acoes(df: pd.DataFrame) -> dict:
    if df.empty:
        return {"TOTAL": 0, "REALIZADO": 0, "EM ANDAMENTO": 0,
                "ATRASADO": 0, "PLANEJADO": 0, "TAXA_REALIZAÇÃO": 0.0}
    counts = df["Status"].value_counts().to_dict()
    total  = len(df)
    taxa   = round(counts.get("REALIZADO", 0) / total * 100, 1)
    return {**counts, "TOTAL": total, "TAXA_REALIZAÇÃO": taxa}
