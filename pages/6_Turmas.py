# pages/6_Turmas.py
import streamlit as st
from db.client import get_supabase
from db.listas import cursos_map, mentores_map
from config import CSS_GLOBAL, TURNOS, MODALIDADES

st.set_page_config(page_title="Turmas — SAEP", page_icon="🏫", layout="wide")
st.markdown(CSS_GLOBAL, unsafe_allow_html=True)

if "usuario" not in st.session_state:
    st.warning("Faça login primeiro.")
    st.stop()

sb = get_supabase()

col_t, col_btn = st.columns([4, 1])
with col_t:
    st.markdown("# 🏫 Turmas Elegíveis")
with col_btn:
    st.markdown("<br>", unsafe_allow_html=True)
    nova = st.button("＋ Nova turma", type="primary", use_container_width=True)

# Listar turmas
res = (
    sb.table("turmas")
    .select("id, codigo, turno, ciclo_saep, status_saep, data_inicio, data_fim, cursos(codigo), mentores(nome)")
    .order("codigo")
    .execute()
)
import pandas as pd
df = pd.DataFrame(res.data)

if not df.empty:
    df["Curso"]   = df["cursos"].apply(lambda x:   x["codigo"] if x else "—")
    df["Mentor"]  = df["mentores"].apply(lambda x: x["nome"]   if x else "—")
    st.dataframe(
        df[["codigo","Curso","turno","ciclo_saep","status_saep","data_inicio","data_fim","Mentor"]].rename(columns={
            "codigo": "Código", "turno": "Turno", "ciclo_saep": "Ciclo",
            "status_saep": "Status SAEP", "data_inicio": "Início", "data_fim": "Fim",
        }),
        use_container_width=True, hide_index=True,
    )
else:
    st.info("Nenhuma turma cadastrada.")

if nova:
    with st.form("form_turma", clear_on_submit=True):
        st.markdown("### Nova Turma")
        c1, c2 = st.columns(2)
        cursos   = cursos_map(sb)
        mentores = mentores_map(sb)
        with c1:
            codigo  = st.text_input("Código *", placeholder="00392.2023.0011")
            turno   = st.selectbox("Turno", TURNOS)
            ciclo   = st.text_input("Ciclo SAEP", placeholder="2026.2")
        with c2:
            curso_s  = st.selectbox("Curso *", list(cursos.keys()))
            mentor_s = st.selectbox("Mentor responsável", list(mentores.keys()))
            d_ini    = st.date_input("Data início")
            d_fim    = st.date_input("Data fim")

        if st.form_submit_button("Salvar", type="primary"):
            if not codigo.strip():
                st.error("Código é obrigatório.")
            else:
                sb.table("turmas").insert({
                    "codigo":      codigo.strip(),
                    "curso_id":    cursos[curso_s],
                    "turno":       turno,
                    "ciclo_saep":  ciclo or None,
                    "data_inicio": str(d_ini),
                    "data_fim":    str(d_fim),
                    "mentor_id":   mentores[mentor_s],
                    "status_saep": "PLANEJADO",
                }).execute()
                st.success("✅ Turma cadastrada!")
                st.rerun()
