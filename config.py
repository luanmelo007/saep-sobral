# config.py
# Fonte única de verdade visual e de constantes do domínio.
# Importe daqui em qualquer página ou componente.

# ── Paleta de status ──────────────────────────────────────────────────────────
COR_STATUS = {
    "PLANEJADO":     "#808080",
    "EM ANDAMENTO":  "#0076D1",
    "REALIZADO":     "#00C896",
    "ATRASADO":      "#E8384F",
    "NÃO REALIZADO": "#F06A00",
}

EMOJI_STATUS = {
    "PLANEJADO":     "⚪",
    "EM ANDAMENTO":  "🔵",
    "REALIZADO":     "✅",
    "ATRASADO":      "🔴",
    "NÃO REALIZADO": "🟠",
}

# ── Paleta de escala de desempenho ────────────────────────────────────────────
COR_ESCALA = {
    "AV":           "#00C896",
    "AD":           "#0076D1",
    "B":            "#F8C500",
    "AB":           "#E8384F",
    "NÃO APLICADA": "#CCCCCC",
}

# ── Opções de domínio ─────────────────────────────────────────────────────────
STATUS_ACAO   = ["PLANEJADO", "EM ANDAMENTO", "REALIZADO", "ATRASADO", "NÃO REALIZADO"]
TIPO_ACAO     = ["MACRO", "TURMA"]
ESCALA_NIVEIS = ["AV", "AD", "B", "AB", "NÃO APLICADA"]
TIPO_AVAL     = ["OBJETIVA", "PRATICA_OFICIAL", "PRATICA_INTERNA", "SIMULADO"]
STATUS_AVAL   = ["PLANEJADO", "REALIZADO", "ATRASADO", "CANCELADO"]
MODALIDADES   = ["PRESENCIAL", "EAD", "NEM", "SEMIPRESENCIAL"]
TURNOS        = ["MANHÃ", "TARDE", "NOITE", "EAD"]

# ── CSS global (injetado em todas as páginas via app.py) ──────────────────────
CSS_GLOBAL = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif !important;
}

/* ── KPI card ── */
.kpi-card {
    background: #FFFFFF;
    border: 1px solid #E8E8E8;
    border-radius: 12px;
    padding: 18px 20px 14px;
    text-align: center;
    box-shadow: 0 1px 4px rgba(0,0,0,.06);
    transition: box-shadow .15s;
}
.kpi-card:hover { box-shadow: 0 3px 10px rgba(0,0,0,.10); }
.kpi-label {
    font-size: 11px;
    font-weight: 600;
    color: #888;
    text-transform: uppercase;
    letter-spacing: .06em;
}
.kpi-value {
    font-size: 30px;
    font-weight: 700;
    color: #1A1A1A;
    line-height: 1.15;
    margin-top: 4px;
}
.kpi-sub { font-size: 12px; color: #AAAAAA; margin-top: 3px; }

/* ── Badge de status ── */
.badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 600;
    color: #FFF;
    white-space: nowrap;
}

/* ── Cabeçalho de seção ── */
.section-header {
    font-size: 12px;
    font-weight: 700;
    color: #666;
    text-transform: uppercase;
    letter-spacing: .09em;
    margin: 28px 0 10px;
    padding-bottom: 8px;
    border-bottom: 2px solid #F0F0F0;
}

/* ── Card de ação ── */
.acao-card {
    background: #FFF;
    border: 1px solid #E8E8E8;
    border-left: 4px solid #0076D1;
    border-radius: 8px;
    padding: 12px 16px;
    margin-bottom: 8px;
    box-shadow: 0 1px 3px rgba(0,0,0,.05);
}
.acao-card.atrasado { border-left-color: #E8384F; background: #FFF8F8; }
.acao-card.realizado { border-left-color: #00C896; opacity: .75; }
.acao-titulo { font-weight: 600; font-size: 14px; color: #1A1A1A; }
.acao-meta   { font-size: 12px; color: #888; margin-top: 4px; }

/* ── Tabelas ── */
.dataframe tbody tr:hover td { background-color: #F5F8FF !important; }

/* ── Sidebar limpa ── */
section[data-testid="stSidebar"] {
    background: #FFFFFF;
    border-right: 1px solid #EBEBEB;
}
</style>
"""
