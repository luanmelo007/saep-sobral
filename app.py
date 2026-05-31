# app.py
import streamlit as st
from db.client import get_supabase
from db.listas import mentor_por_email
from config import CSS_GLOBAL

st.set_page_config(
    page_title="SAEP Sobral",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(CSS_GLOBAL, unsafe_allow_html=True)


# ── Autenticação ──────────────────────────────────────────────────────────────

def tela_login():
    col, _ = st.columns([1.2, 2])
    with col:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.image("https://via.placeholder.com/180x48/0076D1/FFFFFF?text=SAEP+Sobral", width=180)
        st.markdown("### Bem-vindo")
        st.caption("Sistema de Gestão de Entregas — SENAI Sobral")
        st.markdown("<br>", unsafe_allow_html=True)

        email = st.text_input("E-mail institucional", placeholder="nome@docente.senai-ce.org.br")
        senha = st.text_input("Senha", type="password")

        if st.button("Entrar", type="primary", use_container_width=True):
            if not email or not senha:
                st.warning("Preencha e-mail e senha.")
                return
            try:
                sb  = get_supabase()
                res = sb.auth.sign_in_with_password({"email": email, "password": senha})
                mentor = mentor_por_email(sb, email)
                st.session_state["usuario"]       = res.user
                st.session_state["email"]         = email
                st.session_state["mentor"]        = mentor   # dict com id, nome, etc.
                st.session_state["mentor_nome"]   = mentor["nome"] if mentor else email.split("@")[0]
                st.session_state["mentor_id"]     = mentor["id"]   if mentor else None
                st.rerun()
            except Exception:
                st.error("E-mail ou senha incorretos. Verifique suas credenciais.")


if "usuario" not in st.session_state:
    tela_login()
    st.stop()


# ── Sidebar global ────────────────────────────────────────────────────────────

nome_exibido = st.session_state.get("mentor_nome", "Usuário")
st.sidebar.markdown(f"### 📋 SAEP Sobral")
st.sidebar.markdown(f"👤 **{nome_exibido}**")
st.sidebar.divider()

st.sidebar.page_link("app.py",                       label="🏠 Início")
st.sidebar.page_link("pages/1_Dashboard.py",         label="📊 Dashboard")
st.sidebar.page_link("pages/2_Minhas_Tarefas.py",    label="✅ Minhas Tarefas")
st.sidebar.page_link("pages/3_Plano_de_Acao.py",     label="🗃️ Plano de Ação")
st.sidebar.page_link("pages/4_Avaliacoes.py",        label="📋 Avaliações")
st.sidebar.page_link("pages/5_Resultados.py",        label="📈 Resultados")
st.sidebar.page_link("pages/6_Turmas.py",            label="🏫 Turmas")
st.sidebar.page_link("pages/7_Relatorios.py",        label="📊 Relatórios")

st.sidebar.divider()
if st.sidebar.button("🚪 Sair", use_container_width=True):
    st.session_state.clear()
    st.rerun()


# ── Home ──────────────────────────────────────────────────────────────────────

st.title(f"Olá, {nome_exibido} 👋")
st.caption("Use o menu lateral para navegar entre os módulos.")

st.markdown("""
<div style='display:grid; grid-template-columns: repeat(3, 1fr); gap:16px; margin-top:24px'>
  <a href='/Dashboard' target='_self' style='text-decoration:none'>
    <div class='kpi-card' style='text-align:left; cursor:pointer'>
      <div style='font-size:28px'>📊</div>
      <div class='kpi-label' style='margin-top:8px'>Dashboard</div>
      <div style='font-size:13px; color:#555; margin-top:4px'>Visão geral da equipe e alertas</div>
    </div>
  </a>
  <a href='/Minhas_Tarefas' target='_self' style='text-decoration:none'>
    <div class='kpi-card' style='text-align:left; cursor:pointer'>
      <div style='font-size:28px'>✅</div>
      <div class='kpi-label' style='margin-top:8px'>Minhas Tarefas</div>
      <div style='font-size:13px; color:#555; margin-top:4px'>Suas ações e prazos</div>
    </div>
  </a>
  <a href='/Relatorios' target='_self' style='text-decoration:none'>
    <div class='kpi-card' style='text-align:left; cursor:pointer'>
      <div style='font-size:28px'>📈</div>
      <div class='kpi-label' style='margin-top:8px'>Relatórios</div>
      <div style='font-size:13px; color:#555; margin-top:4px'>Filtros, trimestres e exportação</div>
    </div>
  </a>
</div>
""", unsafe_allow_html=True)
