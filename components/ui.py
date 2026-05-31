# components/ui.py
# Widgets reutilizáveis em todas as páginas.

import io
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from config import COR_STATUS, COR_ESCALA, EMOJI_STATUS


# ── KPI card ──────────────────────────────────────────────────────────────────

def kpi(label: str, value, sub: str = "", color: str = "#1A1A1A"):
    st.markdown(
        f"""<div class="kpi-card">
              <div class="kpi-label">{label}</div>
              <div class="kpi-value" style="color:{color}">{value}</div>
              <div class="kpi-sub">{sub}</div>
            </div>""",
        unsafe_allow_html=True,
    )


def kpi_row(metricas: dict):
    """
    Recebe dict {label: (valor, sub?, cor?)} e renderiza uma linha de KPIs.
    Exemplo:
        kpi_row({
            "Total":     (70, "", "#1A1A1A"),
            "Realizadas":(47, "67%", "#00C896"),
        })
    """
    cols = st.columns(len(metricas))
    for col, (label, args) in zip(cols, metricas.items()):
        with col:
            if isinstance(args, (int, float, str)):
                kpi(label, args)
            elif len(args) == 1:
                kpi(label, args[0])
            elif len(args) == 2:
                kpi(label, args[0], sub=str(args[1]))
            else:
                kpi(label, args[0], sub=str(args[1]), color=args[2])


# ── Badge de status ───────────────────────────────────────────────────────────

def badge(texto: str, cor: str = None) -> str:
    c = cor or COR_STATUS.get(texto, "#888")
    return f'<span class="badge" style="background:{c}">{texto}</span>'


def badge_status(status: str) -> str:
    return badge(f"{EMOJI_STATUS.get(status,'')} {status}", COR_STATUS.get(status))


def badge_escala(nivel: str) -> str:
    return badge(nivel, COR_ESCALA.get(nivel, "#888"))


# ── Card de ação ──────────────────────────────────────────────────────────────

def card_acao(row: dict, on_check=None):
    """
    Renderiza um card de ação estilo Asana.
    row: dict com chaves o_que / status / quando_previsto / mentor / turma / curso
    on_check: callback chamado ao clicar em "Marcar como feito"
    """
    css_extra = ""
    if row.get("status") == "ATRASADO":
        css_extra = " atrasado"
    elif row.get("status") == "REALIZADO":
        css_extra = " realizado"

    data_str = str(row.get("quando_previsto", "sem data"))[:10]
    mentor   = row.get("mentor", "—")
    turma    = row.get("turma",  "—")
    curso    = row.get("curso",  "—")

    st.markdown(
        f"""<div class="acao-card{css_extra}">
              <div class="acao-titulo">{row.get('o_que','')}</div>
              <div class="acao-meta">
                  {badge_status(row.get('status',''))} &nbsp;
                  📅 {data_str} &nbsp; 👤 {mentor} &nbsp;
                  📚 {curso} &nbsp; 🏫 {turma}
              </div>
            </div>""",
        unsafe_allow_html=True,
    )


# ── Gráficos ──────────────────────────────────────────────────────────────────

def donut(serie: pd.Series, titulo: str, cores: dict = None, altura: int = 260) -> go.Figure:
    labels = serie.index.tolist()
    values = serie.values.tolist()
    colors = [cores.get(l, "#CCCCCC") for l in labels] if cores else None

    fig = go.Figure(go.Pie(
        labels=labels,
        values=values,
        hole=.58,
        marker_colors=colors,
        textinfo="label+percent",
        textfont_size=11,
        hovertemplate="%{label}: %{value} (%{percent})<extra></extra>",
    ))
    fig.update_layout(
        title=dict(text=titulo, font_size=13, font_color="#444", x=0),
        showlegend=False,
        margin=dict(t=36, b=8, l=8, r=8),
        height=altura,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def barras_por_mentor(df: pd.DataFrame) -> go.Figure:
    if df.empty or "Mentor" not in df.columns or "Status" not in df.columns:
        return go.Figure()

    pivot = (
        df.groupby(["Mentor", "Status"])
        .size()
        .reset_index(name="n")
        .pivot(index="Mentor", columns="Status", values="n")
        .fillna(0)
    )
    fig = go.Figure()
    for status, cor in COR_STATUS.items():
        if status in pivot.columns:
            fig.add_trace(go.Bar(
                name=status, x=pivot.index, y=pivot[status],
                marker_color=cor,
                hovertemplate="%{x}: %{y}<extra>" + status + "</extra>",
            ))
    fig.update_layout(
        barmode="stack",
        title=dict(text="Por Mentor", font_size=13, font_color="#444", x=0),
        xaxis_title="", yaxis_title="",
        legend=dict(orientation="h", y=-0.25, font_size=11),
        height=280,
        margin=dict(t=36, b=70, l=10, r=10),
        paper_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def timeline_mensal(df: pd.DataFrame, col_data: str, titulo: str) -> go.Figure:
    df2 = df.copy()
    df2[col_data] = pd.to_datetime(df2[col_data], errors="coerce")
    df2 = df2.dropna(subset=[col_data])
    if df2.empty:
        return go.Figure()
    df2["mes"] = df2[col_data].dt.to_period("M").astype(str)
    por_mes = df2.groupby("mes").size().reset_index(name="n")
    fig = px.bar(
        por_mes, x="mes", y="n",
        color_discrete_sequence=["#0076D1"],
        labels={"mes": "", "n": ""},
        title=titulo,
    )
    fig.update_layout(
        height=220,
        margin=dict(t=36, b=40, l=10, r=10),
        title=dict(font_size=13, font_color="#444", x=0),
        paper_bgcolor="rgba(0,0,0,0)",
    )
    return fig


# ── Exportação ────────────────────────────────────────────────────────────────

def botoes_exportacao(dataframes: dict[str, pd.DataFrame], prefixo: str):
    """Renderiza botões de download para Excel e CSV."""
    from datetime import date as _date

    st.markdown('<div class="section-header">Exportar</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)

    # Excel
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        for sheet, df in dataframes.items():
            clean = df.copy()
            for col in clean.select_dtypes("object").columns:
                clean[col] = clean[col].str.replace(r"<[^>]+>", "", regex=True)
            clean.to_excel(writer, sheet_name=sheet[:31], index=False)

    with c1:
        st.download_button(
            "⬇️ Excel (.xlsx)",
            data=buf.getvalue(),
            file_name=f"saep_{prefixo}_{_date.today()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

    # CSV
    main_df = list(dataframes.values())[0]
    with c2:
        st.download_button(
            "⬇️ CSV",
            data=main_df.to_csv(index=False).encode("utf-8-sig"),
            file_name=f"saep_{prefixo}_{_date.today()}.csv",
            mime="text/csv",
            use_container_width=True,
        )
