# pages/1_Dashboard.py
import streamlit as st
import pandas as pd
from datetime import date, timedelta

from db.client import get_supabase
from db.acoes import listar_acoes, marcar_atrasadas_automatico
from db.avaliacoes import listar_avaliacoes
from db.listas import mentores_map
from components.ui import kpi_row, donut, barras_por_mentor, badge_status
from config import CSS_GLOBAL, COR_STATUS, EMOJI_STATUS

st.set_page_config(page_title="Dashboard — SAEP", page_icon="📊", layout="wide")
st.markdown(CSS_GLOBAL, unsafe_allow_html=True)

if "usuario" not in st.session_state:
    st.warning("Faça login primeiro.")
    st.stop()

sb = get_supabase()

# Atualiza status de atrasadas silenciosamente
n_atualizadas = marcar_atrasadas_automatico(sb)
if n_atualizadas:
    st.toast(f"⚠️ {n_atualizadas} ação(ões) marcadas como atrasadas.", icon="⚠️")

# ── Dados ─────────────────────────────────────────────────────────────────────
hoje      = date.today()
prox_7    = hoje + timedelta(days=7)
df_acoes  = listar_acoes(sb)
df_avals  = listar_avaliacoes(sb, data_ini=hoje, data_fim=prox_7 + timedelta(days=60))

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("# 📊 Dashboard")
st.caption(f"Situação geral da equipe — {hoje.strftime('%d/%m/%Y')}")

# ── KPIs ──────────────────────────────────────────────────────────────────────
st.markdown('<div class="section-header">Ações — visão geral</div>', unsafe_allow_html=True)

if not df_acoes.empty:
    counts = df_acoes["status"].value_counts().to_dict()
    total  = len(df_acoes)
    taxa   = round(counts.get("REALIZADO", 0) / total * 100, 1)

    kpi_row({
        "Total":        (total,),
        "✅ Realizadas": (counts.get("REALIZADO", 0),    f"{taxa}%",  "#00C896"),
        "🔵 Andamento":  (counts.get("EM ANDAMENTO", 0), "",          "#0076D1"),
        "🔴 Atrasadas":  (counts.get("ATRASADO", 0),     "atenção",   "#E8384F"),
        "⚪ Planejadas":  (counts.get("PLANEJADO", 0),    "",          "#808080"),
    })
else:
    st.info("Nenhuma ação cadastrada ainda.")

# ── Gráficos ──────────────────────────────────────────────────────────────────
if not df_acoes.empty:
    st.markdown('<div class="section-header">Distribuição</div>', unsafe_allow_html=True)
    g1, g2, g3 = st.columns([1, 1, 2])

    with g1:
        st.plotly_chart(
            donut(df_acoes["status"].value_counts(), "Por Status", COR_STATUS),
            use_container_width=True,
        )
    with g2:
        if "curso" in df_acoes.columns:
            st.plotly_chart(
                donut(df_acoes["curso"].value_counts(), "Por Curso"),
                use_container_width=True,
            )
    with g3:
        if "mentor" in df_acoes.columns:
            st.plotly_chart(barras_por_mentor(df_acoes.rename(columns={"status":"Status","mentor":"Mentor"})),
                            use_container_width=True)

# ── Atrasadas — atenção imediata ──────────────────────────────────────────────
atrasadas = df_acoes[df_acoes["status"] == "ATRASADO"] if not df_acoes.empty else pd.DataFrame()

if not atrasadas.empty:
    st.markdown(
        f'<div class="section-header">🔴 Atenção imediata — {len(atrasadas)} ações atrasadas</div>',
        unsafe_allow_html=True,
    )
    for _, row in atrasadas.head(5).iterrows():
        dias = (hoje - pd.to_datetime(row.get("quando_previsto","")).date()) if row.get("quando_previsto") else 0
        st.markdown(
            f"""<div class="acao-card atrasado">
                  <div class="acao-titulo">🔴 {row.get('o_que','—')}</div>
                  <div class="acao-meta">
                      👤 {row.get('mentor','—')} &nbsp;·&nbsp;
                      📚 {row.get('curso','—')} &nbsp;·&nbsp;
                      🏫 {row.get('turma','—')} &nbsp;·&nbsp;
                      📅 venceu há <b>{dias.days if hasattr(dias,'days') else '?'}</b> dia(s)
                  </div>
                </div>""",
            unsafe_allow_html=True,
        )
    if len(atrasadas) > 5:
        st.caption(f"… e mais {len(atrasadas)-5} ações atrasadas. Veja em Plano de Ação.")

# ── Próximas avaliações ───────────────────────────────────────────────────────
prox_avals = df_avals[
    (df_avals["status"].isin(["PLANEJADO","EM ANDAMENTO"])) &
    (pd.to_datetime(df_avals["data_prevista"], errors="coerce") >= pd.Timestamp(hoje))
] if not df_avals.empty else pd.DataFrame()

if not prox_avals.empty:
    st.markdown('<div class="section-header">📅 Próximas avaliações (60 dias)</div>', unsafe_allow_html=True)
    st.dataframe(
        prox_avals[["data_prevista","turma","curso","numero","responsavel","status"]].rename(columns={
            "data_prevista": "Data", "turma": "Turma", "curso": "Curso",
            "numero": "Avaliação", "responsavel": "Responsável", "status": "Status",
        }).head(10),
        use_container_width=True,
        hide_index=True,
    )
