# pages/7_Relatorios.py
import io
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date

from db.client import get_supabase
from db.listas import mentores_map, cursos_map, turmas_map
from db.relatorios import (
    periodos_trimestrais,
    relatorio_acoes,
    relatorio_avaliacoes,
    relatorio_resultados,
    metricas_acoes,
)
from components.ui import kpi_row, donut, barras_por_mentor, timeline_mensal, botoes_exportacao
from config import CSS_GLOBAL, COR_STATUS, COR_ESCALA, STATUS_ACAO, ESCALA_NIVEIS

st.set_page_config(page_title="Relatórios — SAEP", page_icon="📊", layout="wide")
st.markdown(CSS_GLOBAL, unsafe_allow_html=True)

if "usuario" not in st.session_state:
    st.warning("Faça login primeiro.")
    st.stop()

sb = get_supabase()

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("# 📊 Relatórios")
st.caption(f"Acompanhamento de ações, avaliações e resultados — {date.today().strftime('%d/%m/%Y')}")

# ── Chips de período rápido ───────────────────────────────────────────────────
st.markdown('<div class="section-header">⚡ Períodos rápidos</div>', unsafe_allow_html=True)
periodos  = periodos_trimestrais()
opcoes_p  = [k for k in periodos if "Personalizado" not in k]
num_chips = len(opcoes_p)
chip_cols = st.columns(num_chips)

for i, (col, chip) in enumerate(zip(chip_cols, opcoes_p)):
    with col:
        if col.button(chip, key=f"chip_{i}", use_container_width=True):
            st.session_state["periodo_sel"] = chip

if "periodo_sel" in st.session_state:
    st.success(f"📅 **{st.session_state['periodo_sel']}** selecionado — ajuste outros filtros e clique em Gerar.")

st.divider()

# ── Sidebar — filtros ─────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🔍 Filtros")

    tipo_rel = st.radio("Tipo de relatório", ["📋 Ações", "📊 Avaliações", "👤 Resultados por Aluno"],
                        label_visibility="collapsed")
    st.divider()

    st.markdown("### 📅 Período")
    chip_ativo = st.session_state.get("periodo_sel", list(periodos.keys())[0])
    periodo_sel = st.selectbox("Período", list(periodos.keys()),
                               index=list(periodos.keys()).index(chip_ativo) if chip_ativo in periodos else 0,
                               label_visibility="collapsed")

    d_ini_pre, d_fim_pre = periodos[periodo_sel]
    if periodo_sel == "Personalizado":
        d_ini = st.date_input("De",  value=date.today().replace(day=1))
        d_fim = st.date_input("Até", value=date.today())
    else:
        d_ini, d_fim = d_ini_pre, d_fim_pre
        st.caption(f"📆 {d_ini.strftime('%d/%m/%Y')} → {d_fim.strftime('%d/%m/%Y')}")

    st.divider()
    st.markdown("### 👥 Equipe")
    mentores  = mentores_map(sb)
    m_sels    = st.multiselect("Mentor(es)", list(mentores.keys()))
    m_ids     = [mentores[m] for m in m_sels] if m_sels else None

    st.markdown("### 📚 Curso / Turma")
    cursos    = cursos_map(sb)
    c_sels    = st.multiselect("Curso(s)", list(cursos.keys()))
    c_ids     = [cursos[c] for c in c_sels] if c_sels else None
    turmas    = turmas_map(sb, curso_ids=c_ids)
    t_sels    = st.multiselect("Turma(s)", list(turmas.keys()))
    t_ids     = [turmas[t] for t in t_sels] if t_sels else None

    st.divider()
    st.markdown("### 🏷️ Status")
    s_sels    = st.multiselect("Status", STATUS_ACAO)
    s_filtro  = s_sels if s_sels else None

    extras = {}
    if tipo_rel == "📋 Ações":
        tipo_a = st.multiselect("Tipo de ação", ["MACRO","TURMA"])
        extras["tipo"] = tipo_a if tipo_a else None
    if tipo_rel == "👤 Resultados por Aluno":
        esc_s  = st.multiselect("Nível", ESCALA_NIVEIS)
        extras["escalas"] = esc_s if esc_s else None

    gerar = st.button("🔍 Gerar relatório", type="primary", use_container_width=True)

# ── Relatório ─────────────────────────────────────────────────────────────────
if not gerar:
    st.markdown("""
    <div style='text-align:center; color:#AAA; padding:80px 0'>
        <div style='font-size:48px'>📋</div>
        <div style='font-weight:600; margin-top:12px'>Configure os filtros e clique em <b>Gerar relatório</b></div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ── Ações ─────────────────────────────────────────────────────────────────────
if tipo_rel == "📋 Ações":
    st.subheader("📋 Ações Pedagógicas")
    df = relatorio_acoes(sb, d_ini, d_fim, m_ids, c_ids, t_ids, s_filtro, extras.get("tipo"))
    met = metricas_acoes(df)

    kpi_row({
        "Total":          (met["TOTAL"],),
        "✅ Realizadas":   (met.get("REALIZADO",0),    f"{met['TAXA_REALIZAÇÃO']}%", "#00C896"),
        "🔵 Em andamento": (met.get("EM ANDAMENTO",0), "",                           "#0076D1"),
        "🔴 Atrasadas":    (met.get("ATRASADO",0),     "",                           "#E8384F"),
        "⚪ Planejadas":    (met.get("PLANEJADO",0),    "",                           "#808080"),
    })

    if not df.empty:
        g1, g2, g3 = st.columns([1,1,2])
        with g1: st.plotly_chart(donut(df["Status"].value_counts(), "Por Status", COR_STATUS), use_container_width=True)
        with g2: st.plotly_chart(donut(df["Curso"].value_counts(),  "Por Curso"),              use_container_width=True)
        with g3: st.plotly_chart(barras_por_mentor(df),                                        use_container_width=True)

        st.plotly_chart(timeline_mensal(df, "Previsto", "Ações por mês"), use_container_width=True)

        st.markdown('<div class="section-header">Detalhamento</div>', unsafe_allow_html=True)
        grupo_por = st.selectbox("Agrupar por", ["—","Mentor","Curso","Status"])
        if grupo_por != "—":
            for g, gdf in df.groupby(grupo_por):
                with st.expander(f"**{g}** — {len(gdf)} ações", expanded=True):
                    st.dataframe(gdf.drop(columns=[grupo_por], errors="ignore"), use_container_width=True, hide_index=True)
        else:
            st.dataframe(df, use_container_width=True, hide_index=True)

        botoes_exportacao({"Ações": df}, "acoes")
    else:
        st.info("Nenhuma ação encontrada para os filtros selecionados.")

# ── Avaliações ────────────────────────────────────────────────────────────────
elif tipo_rel == "📊 Avaliações":
    st.subheader("📊 Avaliações Diagnósticas")
    df = relatorio_avaliacoes(sb, d_ini, d_fim, m_ids, t_ids, s_filtro)

    if not df.empty:
        c = df["Status"].value_counts().to_dict()
        kpi_row({
            "Total":        (len(df),),
            "✅ Realizadas": (c.get("REALIZADO",0), "", "#00C896"),
            "⚪ Planejadas":  (c.get("PLANEJADO",0), "", "#808080"),
            "🔴 Atrasadas":  (c.get("ATRASADO",0),  "", "#E8384F"),
        })

        g1, g2 = st.columns(2)
        with g1: st.plotly_chart(donut(df["Status"].value_counts(), "Por Status", COR_STATUS), use_container_width=True)
        with g2:
            real = df[df["Status"]=="REALIZADO"].copy()
            if not real.empty:
                real["res_num"] = real["Resultado %"].str.replace("%","").astype(float, errors="ignore")
                fig = px.bar(real.groupby("Curso")["res_num"].mean().reset_index(),
                             x="Curso", y="res_num", color="res_num",
                             color_continuous_scale=["#E8384F","#F8C500","#00C896"],
                             range_color=[0,100], title="Resultado médio por Curso (%)")
                fig.update_layout(height=260, margin=dict(t=40,b=40))
                st.plotly_chart(fig, use_container_width=True)

        st.dataframe(df, use_container_width=True, hide_index=True)
        botoes_exportacao({"Avaliações": df}, "avaliacoes")
    else:
        st.info("Nenhuma avaliação encontrada.")

# ── Resultados ────────────────────────────────────────────────────────────────
else:
    st.subheader("👤 Resultados por Aluno")
    df = relatorio_resultados(sb, d_ini, d_fim, t_ids, extras.get("escalas"))

    if not df.empty:
        dist  = df["Nível"].value_counts()
        total = len(df)
        kpi_row({
            "Total":       (total,),
            "AV Avançado": (dist.get("AV",0), f"{dist.get('AV',0)/total*100:.0f}%", "#00C896"),
            "AD Adequado": (dist.get("AD",0), f"{dist.get('AD',0)/total*100:.0f}%", "#0076D1"),
            "B Básico":    (dist.get("B",0),  f"{dist.get('B',0)/total*100:.0f}%",  "#F8C500"),
            "AB Abaixo":   (dist.get("AB",0), f"{dist.get('AB',0)/total*100:.0f}%", "#E8384F"),
        })

        g1, g2 = st.columns(2)
        with g1: st.plotly_chart(donut(dist, "Por Nível", COR_ESCALA), use_container_width=True)

        em_risco = df[df["Nível"].isin(["AB","B"])]
        if not em_risco.empty:
            st.markdown(f'<div class="section-header">⚠️ Alunos que precisam de intervenção ({len(em_risco)})</div>', unsafe_allow_html=True)
            st.dataframe(em_risco, use_container_width=True, hide_index=True)

        with st.expander("Ver todos"):
            st.dataframe(df, use_container_width=True, hide_index=True)

        botoes_exportacao({"Resultados": df}, "resultados")
    else:
        st.info("Nenhum resultado encontrado.")
