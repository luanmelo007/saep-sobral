# pages/2_Minhas_Tarefas.py
import streamlit as st
import pandas as pd
from datetime import date, timedelta

from db.client import get_supabase
from db.acoes import listar_acoes, atualizar_status, criar_acao
from db.listas import cursos_map, turmas_map, mentores_map
from components.ui import badge_status, kpi_row
from config import CSS_GLOBAL, COR_STATUS, STATUS_ACAO, TIPO_ACAO

st.set_page_config(page_title="Minhas Tarefas — SAEP", page_icon="✅", layout="wide")
st.markdown(CSS_GLOBAL, unsafe_allow_html=True)

if "usuario" not in st.session_state:
    st.warning("Faça login primeiro.")
    st.stop()

sb       = get_supabase()
mid      = st.session_state.get("mentor_id")
mnome    = st.session_state.get("mentor_nome", "Você")

# ── Header ────────────────────────────────────────────────────────────────────
col_t, col_btn = st.columns([4, 1])
with col_t:
    st.markdown(f"# ✅ Tarefas de {mnome}")
with col_btn:
    st.markdown("<br>", unsafe_allow_html=True)
    nova = st.button("＋ Nova ação", type="primary", use_container_width=True)

# ── Filtro de período ─────────────────────────────────────────────────────────
hoje    = date.today()
filtros = st.radio(
    "Período",
    ["Todas", "Esta semana", "Este mês", "Atrasadas"],
    horizontal=True,
    label_visibility="collapsed",
)

data_ini = None
data_fim = None
status_f = None

if filtros == "Esta semana":
    data_ini = hoje
    data_fim = hoje + timedelta(days=7)
elif filtros == "Este mês":
    data_ini = hoje.replace(day=1)
    data_fim = (hoje.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
elif filtros == "Atrasadas":
    status_f = ["ATRASADO"]

# ── Dados ─────────────────────────────────────────────────────────────────────
df = listar_acoes(
    sb,
    mentor_id=mid,
    status=status_f,
    data_ini=data_ini,
    data_fim=data_fim,
)

# ── KPIs ──────────────────────────────────────────────────────────────────────
if not df.empty:
    c = df["status"].value_counts().to_dict()
    kpi_row({
        "Total":        (len(df),),
        "✅ Realizadas": (c.get("REALIZADO", 0),    "", "#00C896"),
        "🔴 Atrasadas":  (c.get("ATRASADO", 0),     "", "#E8384F"),
        "🔵 Andamento":  (c.get("EM ANDAMENTO", 0), "", "#0076D1"),
        "⚪ Planejadas":  (c.get("PLANEJADO", 0),    "", "#808080"),
    })

st.markdown("---")

# ── Lista de tarefas agrupada por status ──────────────────────────────────────
ORDEM_STATUS = ["ATRASADO", "EM ANDAMENTO", "PLANEJADO", "REALIZADO", "NÃO REALIZADO"]

if df.empty:
    st.info("Nenhuma tarefa encontrada para os filtros selecionados.")
else:
    for s in ORDEM_STATUS:
        grupo = df[df["status"] == s]
        if grupo.empty:
            continue

        cor   = COR_STATUS.get(s, "#888")
        label = f"**{s}** — {len(grupo)} ação(ões)"
        aberto = s != "REALIZADO"

        with st.expander(label, expanded=aberto):
            for _, row in grupo.iterrows():
                c1, c2, c3 = st.columns([5, 1.5, 1.5])
                with c1:
                    data_str = str(row.get("quando_previsto","sem data"))[:10]
                    curso    = row.get("curso","—")
                    turma    = row.get("turma","—")
                    st.markdown(
                        f"""<div style='padding: 6px 0'>
                              <span style='font-weight:600'>{row.get('o_que','')}</span><br>
                              <span style='font-size:12px; color:#888'>
                                  📅 {data_str} &nbsp;·&nbsp; 📚 {curso} &nbsp;·&nbsp; 🏫 {turma}
                              </span>
                            </div>""",
                        unsafe_allow_html=True,
                    )
                with c2:
                    novo_s = st.selectbox(
                        "Status",
                        STATUS_ACAO,
                        index=STATUS_ACAO.index(s) if s in STATUS_ACAO else 0,
                        key=f"sel_{row['id']}",
                        label_visibility="collapsed",
                    )
                    if novo_s != s:
                        atualizar_status(sb, row["id"], novo_s)
                        st.rerun()
                with c3:
                    if st.button("Editar", key=f"ed_{row['id']}", use_container_width=True):
                        st.session_state["editar_acao_id"] = row["id"]

# ── Modal de nova ação ────────────────────────────────────────────────────────
if nova or st.session_state.get("editar_acao_id"):
    with st.form("form_acao", clear_on_submit=True):
        st.markdown("### Nova Ação")
        o_que   = st.text_input("O quê *", placeholder="Ex: Aulão SAEP — Eletrotécnica")
        col1, col2 = st.columns(2)
        with col1:
            tipo    = st.selectbox("Tipo", TIPO_ACAO)
            quando  = st.date_input("Quando (previsto)", value=hoje + timedelta(days=7))
            onde    = st.text_input("Onde")
        with col2:
            cursos  = cursos_map(sb)
            curso_s = st.selectbox("Curso", ["—"] + list(cursos.keys()))
            turmas  = turmas_map(sb, curso_ids=[cursos[curso_s]] if curso_s != "—" else None)
            turma_s = st.selectbox("Turma", ["—"] + list(turmas.keys()))

        porque  = st.text_area("Por quê", height=60)
        como    = st.text_area("Como",    height=60)

        if st.form_submit_button("Salvar", type="primary"):
            if not o_que.strip():
                st.error("O campo 'O quê' é obrigatório.")
            else:
                criar_acao(sb, {
                    "o_que":           o_que.strip(),
                    "tipo":            tipo,
                    "quando_previsto": str(quando),
                    "onde":            onde or None,
                    "porque":          porque or None,
                    "como":            como or None,
                    "quem_id":         mid,
                    "curso_id":        cursos.get(curso_s),
                    "turma_id":        turmas.get(turma_s),
                    "status":          "PLANEJADO",
                })
                st.success("✅ Ação criada!")
                st.rerun()
