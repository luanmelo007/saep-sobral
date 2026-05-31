# pages/4_Avaliacoes.py
import streamlit as st
import pandas as pd
from datetime import date, timedelta

from db.client import get_supabase
from db.avaliacoes import listar_avaliacoes, criar_avaliacao, atualizar_avaliacao
from db.listas import turmas_map, mentores_map
from components.ui import kpi_row, badge_status
from config import CSS_GLOBAL, STATUS_AVAL, TIPO_AVAL, COR_STATUS

st.set_page_config(page_title="Avaliações — SAEP", page_icon="📋", layout="wide")
st.markdown(CSS_GLOBAL, unsafe_allow_html=True)

if "usuario" not in st.session_state:
    st.warning("Faça login primeiro.")
    st.stop()

sb   = get_supabase()
hoje = date.today()

col_t, col_btn = st.columns([4, 1])
with col_t:
    st.markdown("# 📋 Avaliações Diagnósticas")
with col_btn:
    st.markdown("<br>", unsafe_allow_html=True)
    nova = st.button("＋ Nova avaliação", type="primary", use_container_width=True)

# Filtro rápido
periodo = st.radio(
    "", ["Próximos 60 dias", "Este ano", "Todas"],
    horizontal=True, label_visibility="collapsed",
)
if periodo == "Próximos 60 dias":
    d_ini, d_fim = hoje, hoje + timedelta(days=60)
elif periodo == "Este ano":
    d_ini, d_fim = date(hoje.year, 1, 1), date(hoje.year, 12, 31)
else:
    d_ini, d_fim = None, None

df = listar_avaliacoes(sb, data_ini=d_ini, data_fim=d_fim)

if not df.empty:
    c = df["status"].value_counts().to_dict()
    kpi_row({
        "Total":        (len(df),),
        "✅ Realizadas": (c.get("REALIZADO", 0), "", "#00C896"),
        "🔴 Atrasadas":  (c.get("ATRASADO", 0),  "", "#E8384F"),
        "⚪ Planejadas":  (c.get("PLANEJADO", 0), "", "#808080"),
    })
    st.markdown("---")

    colunas = ["data_prevista","data_realizada","status","curso","turma",
               "numero","tipo","responsavel","resultado_%","observacoes"]
    colunas = [c for c in colunas if c in df.columns]
    st.dataframe(df[colunas], use_container_width=True, hide_index=True)
else:
    st.info("Nenhuma avaliação encontrada para o período selecionado.")

if nova:
    with st.form("form_aval", clear_on_submit=True):
        st.markdown("### Nova Avaliação")
        turmas = turmas_map(sb)
        mentores = mentores_map(sb)
        c1, c2 = st.columns(2)
        with c1:
            turma_s = st.selectbox("Turma *", list(turmas.keys()))
            numero  = st.text_input("Nº Avaliação *", placeholder="1ª Diagnóstica, PO, PP...")
            tipo    = st.selectbox("Tipo", TIPO_AVAL)
        with c2:
            resp    = st.selectbox("Responsável", list(mentores.keys()))
            quando  = st.date_input("Data prevista", value=hoje + timedelta(days=14))
            local   = st.text_input("Local")

        if st.form_submit_button("Salvar", type="primary"):
            if not turma_s or not numero:
                st.error("Turma e Nº de Avaliação são obrigatórios.")
            else:
                criar_avaliacao(sb, {
                    "turma_id":       turmas[turma_s],
                    "numero":         numero.strip(),
                    "tipo":           tipo,
                    "responsavel_id": mentores[resp],
                    "data_prevista":  str(quando),
                    "local":          local or None,
                    "status":         "PLANEJADO",
                })
                st.success("✅ Avaliação criada!")
                st.rerun()
