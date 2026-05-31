# SAEP Sobral — Sistema de Gestão de Entregas

Sistema de acompanhamento de ações pedagógicas, avaliações diagnósticas e resultados por aluno para a equipe de mentores do SAEP no SENAI Sobral.

**Stack:** Python 3.12 · Streamlit · Supabase · Plotly

---

## Configuração inicial

```bash
# 1. Clonar e entrar na pasta
git clone https://github.com/SEU_USUARIO/saep-sobral.git
cd saep-sobral

# 2. Criar e ativar ambiente virtual
python -m venv .venv
source .venv/bin/activate   # Linux/Mac
.venv\Scripts\activate      # Windows

# 3. Instalar dependências
pip install -r requirements.txt

# 4. Configurar credenciais
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Edite secrets.toml com suas credenciais do Supabase

# 5. Criar o banco de dados
# Execute scripts/schema.sql no SQL Editor do Supabase

# 6. Rodar localmente
streamlit run app.py
```

## Estrutura

```
app.py              → entrada + autenticação
pages/              → módulos (Dashboard, Tarefas, Kanban, Avaliações, Resultados, Turmas, Relatórios)
db/                 → queries Supabase por domínio
components/         → widgets reutilizáveis
scripts/            → schema SQL e migração da planilha
```

## Equipe

Luan · Raimundo · Lucilani · Décio · Claudecir — SENAI Sobral / CFP José Euclides
