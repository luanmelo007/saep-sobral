# pages/3_Plano_de_Acao.py
import streamlit as st
import pandas as pd
from datetime import date, timedelta

from db.client import get_supabase
from db.acoes import listar_acoes, atualizar_status, criar_acao, excluir_acao
from db.listas import cursos_map, turmas_map, mentores_map
from components.ui import badge_status
from config import CSS_GLOBAL, COR_STATUS, STATUS_ACAO, TIPO_ACAO

st.set_page_config(page_title="Plano de Ação — SAEP", page_icon="🗃️", layout="wide")
st.markdown(CSS_GLOBAL, unsafe_allow_html=True)

if "usuario" not in st.session_state:
    st.warning("Faça login primeiro.")
    st.stop()

sb = get_supabase()

# ── Header ────────────────────────────────────────────────────────────────────
col_t, col_f, col_btn = st.columns([3, 2, 1])
with col_t:
    st.markdown("# 🗃️ Plano de Ação")
with col_f:
    st.markdown("<br>", unsafe_allow_html=True)
    view = st.radio("Visão", ["Kanban", "Lista"], horizontal=True, label_visibility="collapsed")
with col_btn:
    st.markdown("<br>", unsafe_allow_html=True)
    nova = st.button("＋ Nova ação", type="primary", use_container_width=True)

# ── Filtros laterais ──────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Filtros")
    mentores = mentores_map(sb)
    mentor_s = st.multiselect("Mentor", list(mentores.keys()))
    cursos   = cursos_map(sb)
    curso_s  = st.multiselect("Curso", list(cursos.keys()))
    tipo_s   = st.multiselect("Tipo", TIPO_ACAO)
    st.divider()
    if st.button("Limpar filtros"):
        st.rerun()

mentor_ids = [mentores[m] for m in mentor_s] if mentor_s else None
curso_ids  = [cursos[c]   for c in curso_s]  if curso_s  else None

df = listar_acoes(
    sb,
    mentor_id=mentor_ids[0] if mentor_ids and len(mentor_ids) == 1 else None,
    curso_id=curso_ids[0]   if curso_ids  and len(curso_ids)  == 1 else None,
    tipo=tipo_s if tipo_s else None,
)

# ── Kanban ────────────────────────────────────────────────────────────────────
if view == "Kanban":
    colunas_status = ["PLANEJADO", "EM ANDAMENTO", "ATRASADO", "REALIZADO"]
    cols = st.columns(len(colunas_status))

    for col, s in zip(cols, colunas_status):
        grupo = df[df["status"] == s] if not df.empty else pd.DataFrame()
        cor   = COR_STATUS.get(s, "#888")
        with col:
            st.markdown(
                f'<div style="font-weight:700; font-size:12px; color:{cor}; text-transform:uppercase; '
                f'letter-spacing:.08em; padding:8px 0; border-bottom:3px solid {cor}; margin-bottom:12px">'
                f'{s} ({len(grupo)})</div>',
                unsafe_allow_html=True,
            )
            for _, row in grupo.iterrows():
                with st.container(border=True):
                    st.markdown(f"**{row.get('o_que','—')}**")
                    st.caption(
                        f"👤 {row.get('mentor','—')}  "
                        f"📅 {str(row.get('quando_previsto',''))[:10]}"
                    )
                    novo_s = st.selectbox(
                        "", STATUS_ACAO,
                        index=STATUS_ACAO.index(s) if s in STATUS_ACAO else 0,
                        key=f"k_{row['id']}",
                        label_visibility="collapsed",
                    )
                    if novo_s != s:
                        atualizar_status(sb, row["id"], novo_s)
                        st.rerun()

# ── Lista ─────────────────────────────────────────────────────────────────────
else:
    if df.empty:
        st.info("Nenhuma ação encontrada.")
    else:
        colunas_exib = ["quando_previsto","status","tipo","o_que","mentor","curso","turma","observacoes"]
        colunas_exib = [c for c in colunas_exib if c in df.columns]
        st.dataframe(df[colunas_exib], use_container_width=True, hide_index=True)

# ── Form nova ação ────────────────────────────────────────────────────────────
if nova:
    with st.form("form_nova_acao", clear_on_submit=True):
        st.markdown("### Nova Ação")
        o_que  = st.text_input("O quê *")
        c1, c2 = st.columns(2)
        with c1:
            tipo   = st.selectbox("Tipo", TIPO_ACAO)
            quando = st.date_input("Quando", value=date.today() + timedelta(days=7))
        with c2:
            curso_sel = st.selectbox("Curso", ["—"] + list(cursos_map(sb).keys()))
            resp_sel  = st.selectbox("Responsável", list(mentores_map(sb).keys()))
        porque = st.text_area("Por quê", height=60)
        como   = st.text_area("Como",    height=60)

        if st.form_submit_button("Salvar", type="primary"):
            if not o_que.strip():
                st.error("O campo 'O quê' é obrigatório.")
            else:
                cmap = cursos_map(sb)
                mmap = mentores_map(sb)
                criar_acao(sb, {
                    "o_que":           o_que.strip(),
                    "tipo":            tipo,
                    "quando_previsto": str(quando),
                    "porque":          porque or None,
                    "como":            como or None,
                    "quem_id":         mmap.get(resp_sel),
                    "curso_id":        cmap.get(curso_sel),
                    "status":          "PLANEJADO",
                })
                st.success("✅ Ação criada!")
                st.rerun()
