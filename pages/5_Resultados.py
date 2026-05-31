# pages/5_Resultados.py
import streamlit as st
import pandas as pd

from db.client import get_supabase
from db.resultados import listar_resultados, upsert_resultados, distribuicao_escala
from db.listas import turmas_map, avaliacoes_map
from components.ui import kpi_row, donut
from config import CSS_GLOBAL, COR_ESCALA, ESCALA_NIVEIS

st.set_page_config(page_title="Resultados — SAEP", page_icon="📈", layout="wide")
st.markdown(CSS_GLOBAL, unsafe_allow_html=True)

if "usuario" not in st.session_state:
    st.warning("Faça login primeiro.")
    st.stop()

sb = get_supabase()
st.markdown("# 📈 Resultados por Turma")

c1, c2 = st.columns(2)
with c1:
    turmas   = turmas_map(sb)
    turma_s  = st.selectbox("Turma", ["— selecione —"] + list(turmas.keys()))
with c2:
    aval_s   = None
    if turma_s and turma_s != "— selecione —":
        avals    = avaliacoes_map(sb, turmas[turma_s])
        aval_s   = st.selectbox("Avaliação", ["— selecione —"] + list(avals.keys()))

if not turma_s or turma_s == "— selecione —":
    st.info("Selecione uma turma para ver os resultados.")
    st.stop()

if not aval_s or aval_s == "— selecione —":
    st.info("Selecione uma avaliação.")
    st.stop()

aval_id = avals[aval_s]
df = listar_resultados(sb, aval_id)

if df.empty:
    st.info("Nenhum resultado lançado para esta avaliação.")
else:
    dist  = df["escala"].value_counts()
    total = len(df)

    st.markdown('<div class="section-header">Distribuição de desempenho</div>', unsafe_allow_html=True)
    kpi_row({
        "Total":        (total,),
        "AV — Avançado": (dist.get("AV",0), f"{dist.get('AV',0)/total*100:.0f}%", "#00C896"),
        "AD — Adequado": (dist.get("AD",0), f"{dist.get('AD',0)/total*100:.0f}%", "#0076D1"),
        "B — Básico":    (dist.get("B",0),  f"{dist.get('B',0)/total*100:.0f}%",  "#F8C500"),
        "AB — Abaixo":   (dist.get("AB",0), f"{dist.get('AB',0)/total*100:.0f}%", "#E8384F"),
    })

    g1, g2 = st.columns(2)
    with g1:
        st.plotly_chart(donut(dist, "Distribuição por Nível", COR_ESCALA), use_container_width=True)
    with g2:
        em_risco = df[df["escala"].isin(["AB","B"])]
        if not em_risco.empty:
            st.markdown(f"**⚠️ {len(em_risco)} aluno(s) em AB ou B — precisam de intervenção**")
            st.dataframe(
                em_risco[["nome_aluno","pontuacao","escala","dificuldades","intervencao"]],
                use_container_width=True, hide_index=True,
            )

    st.markdown('<div class="section-header">Todos os alunos</div>', unsafe_allow_html=True)
    st.dataframe(
        df[["nome_aluno","pontuacao","escala","dificuldades","intervencao"]],
        use_container_width=True, hide_index=True,
    )

# ── Lançar/importar resultados ────────────────────────────────────────────────
with st.expander("📥 Lançar resultado de aluno"):
    with st.form("form_resultado", clear_on_submit=True):
        c1, c2, c3 = st.columns([3, 1, 1])
        with c1: nome     = st.text_input("Nome do aluno")
        with c2: pont     = st.number_input("Pontuação", min_value=0.0, max_value=1000.0, step=0.1)
        with c3: escala_s = st.selectbox("Nível", ESCALA_NIVEIS)
        dific = st.text_input("Dificuldades identificadas")
        inter = st.text_input("Intervenção proposta")

        if st.form_submit_button("Salvar resultado", type="primary"):
            if not nome.strip():
                st.error("Nome do aluno é obrigatório.")
            else:
                upsert_resultados(sb, [{
                    "avaliacao_id": aval_id,
                    "nome_aluno":   nome.strip(),
                    "pontuacao":    pont,
                    "escala":       escala_s,
                    "dificuldades": dific or None,
                    "intervencao":  inter or None,
                }])
                st.success("✅ Resultado salvo!")
                st.rerun()
