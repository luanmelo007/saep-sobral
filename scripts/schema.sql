-- ═══════════════════════════════════════════════════════════════════════
-- SAEP Sobral — Schema completo do banco de dados
-- Execute no SQL Editor do Supabase (em ordem)
-- ═══════════════════════════════════════════════════════════════════════

-- 1. MENTORES
CREATE TABLE mentores (
    id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nome      TEXT NOT NULL,
    email     TEXT UNIQUE NOT NULL,
    ativo     BOOLEAN DEFAULT true,
    criado_em TIMESTAMPTZ DEFAULT now()
);

-- 2. CURSOS
CREATE TABLE cursos (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    codigo        TEXT NOT NULL,
    nome_completo TEXT NOT NULL,
    modalidade    TEXT CHECK (modalidade IN ('PRESENCIAL','EAD','NEM','SEMIPRESENCIAL')),
    mentor_id     UUID REFERENCES mentores(id)
);

-- 3. TURMAS
CREATE TABLE turmas (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    codigo      TEXT NOT NULL UNIQUE,
    curso_id    UUID REFERENCES cursos(id),
    turno       TEXT CHECK (turno IN ('MANHÃ','TARDE','NOITE','EAD')),
    data_inicio DATE,
    data_fim    DATE,
    ciclo_saep  TEXT,
    status_saep TEXT DEFAULT 'NÃO ELEGÍVEL',
    mentor_id   UUID REFERENCES mentores(id)
);

-- 4. AÇÕES
CREATE TABLE acoes (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tipo             TEXT NOT NULL CHECK (tipo IN ('MACRO','TURMA')),
    turma_id         UUID REFERENCES turmas(id),
    curso_id         UUID REFERENCES cursos(id),
    o_que            TEXT NOT NULL,
    porque           TEXT,
    onde             TEXT,
    quem_id          UUID REFERENCES mentores(id),
    quando_previsto  DATE,
    como             TEXT,
    status           TEXT NOT NULL DEFAULT 'PLANEJADO'
                     CHECK (status IN ('PLANEJADO','EM ANDAMENTO','REALIZADO','ATRASADO','NÃO REALIZADO')),
    data_realizacao  DATE,
    observacoes      TEXT,
    encaminhamentos  TEXT,
    criado_em        TIMESTAMPTZ DEFAULT now(),
    atualizado_em    TIMESTAMPTZ DEFAULT now()
);

-- Trigger: atualiza atualizado_em
CREATE OR REPLACE FUNCTION fn_set_atualizado_em()
RETURNS TRIGGER AS $$
BEGIN NEW.atualizado_em = now(); RETURN NEW; END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_acoes_atualizado
    BEFORE UPDATE ON acoes
    FOR EACH ROW EXECUTE FUNCTION fn_set_atualizado_em();

-- 5. HISTÓRICO DE AÇÕES (auditoria automática)
CREATE TABLE historico_acoes (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    acao_id      UUID REFERENCES acoes(id) ON DELETE CASCADE,
    status_de    TEXT,
    status_para  TEXT NOT NULL,
    nota         TEXT,
    alterado_em  TIMESTAMPTZ DEFAULT now(),
    alterado_por TEXT
);

CREATE OR REPLACE FUNCTION fn_historico_acao()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.status IS DISTINCT FROM NEW.status THEN
        INSERT INTO historico_acoes (acao_id, status_de, status_para, alterado_por)
        VALUES (
            NEW.id, OLD.status, NEW.status,
            current_setting('request.jwt.claims', true)::json->>'email'
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_historico_acao
    AFTER UPDATE ON acoes
    FOR EACH ROW EXECUTE FUNCTION fn_historico_acao();

-- 6. AVALIAÇÕES
CREATE TABLE avaliacoes (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    turma_id         UUID REFERENCES turmas(id) NOT NULL,
    numero           TEXT NOT NULL,
    tipo             TEXT DEFAULT 'OBJETIVA'
                     CHECK (tipo IN ('OBJETIVA','PRATICA_OFICIAL','PRATICA_INTERNA','SIMULADO')),
    local            TEXT,
    responsavel_id   UUID REFERENCES mentores(id),
    data_prevista    DATE,
    data_realizada   DATE,
    status           TEXT DEFAULT 'PLANEJADO'
                     CHECK (status IN ('PLANEJADO','REALIZADO','ATRASADO','CANCELADO')),
    resultado_medio  FLOAT CHECK (resultado_medio BETWEEN 0 AND 1),
    ciclo            TEXT,
    link_forms       TEXT,
    observacoes      TEXT
);

-- 7. RESULTADOS POR ALUNO
CREATE TABLE resultados_alunos (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    avaliacao_id UUID REFERENCES avaliacoes(id) ON DELETE CASCADE NOT NULL,
    nome_aluno   TEXT NOT NULL,
    pontuacao    FLOAT,
    escala       TEXT CHECK (escala IN ('AB','B','AD','AV','NÃO APLICADA')),
    dificuldades TEXT,
    intervencao  TEXT,
    UNIQUE (avaliacao_id, nome_aluno)
);

-- 8. ESCALAS DE RENDIMENTO
CREATE TABLE escalas_rendimento (
    id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    curso_id  UUID REFERENCES cursos(id),
    nivel     TEXT NOT NULL CHECK (nivel IN ('AB','B','AD','AV')),
    valor_min FLOAT NOT NULL,
    valor_max FLOAT NOT NULL
);

-- ═══════════════════════════════════════════════════════════════════════
-- ROW LEVEL SECURITY
-- ═══════════════════════════════════════════════════════════════════════

ALTER TABLE mentores           ENABLE ROW LEVEL SECURITY;
ALTER TABLE cursos             ENABLE ROW LEVEL SECURITY;
ALTER TABLE turmas             ENABLE ROW LEVEL SECURITY;
ALTER TABLE acoes              ENABLE ROW LEVEL SECURITY;
ALTER TABLE historico_acoes    ENABLE ROW LEVEL SECURITY;
ALTER TABLE avaliacoes         ENABLE ROW LEVEL SECURITY;
ALTER TABLE resultados_alunos  ENABLE ROW LEVEL SECURITY;
ALTER TABLE escalas_rendimento ENABLE ROW LEVEL SECURITY;

-- Tabelas de referência: leitura pública
CREATE POLICY "leitura_mentores"   ON mentores           FOR SELECT USING (true);
CREATE POLICY "leitura_cursos"     ON cursos             FOR SELECT USING (true);
CREATE POLICY "leitura_turmas"     ON turmas             FOR SELECT USING (true);
CREATE POLICY "leitura_escalas"    ON escalas_rendimento FOR SELECT USING (true);

-- Ações: todos leem, cada mentor edita apenas as suas
CREATE POLICY "leitura_acoes"      ON acoes FOR SELECT USING (true);
CREATE POLICY "insert_acoes"       ON acoes FOR INSERT WITH CHECK (true);
CREATE POLICY "update_acoes_proprio" ON acoes FOR UPDATE
    USING (quem_id = (SELECT id FROM mentores WHERE email = auth.email()));
CREATE POLICY "delete_acoes_proprio" ON acoes FOR DELETE
    USING (quem_id = (SELECT id FROM mentores WHERE email = auth.email()));

-- Avaliações e resultados: acesso geral autenticado
CREATE POLICY "auth_avaliacoes"    ON avaliacoes         FOR ALL USING (auth.role() = 'authenticated');
CREATE POLICY "auth_resultados"    ON resultados_alunos  FOR ALL USING (auth.role() = 'authenticated');
CREATE POLICY "auth_historico"     ON historico_acoes    FOR ALL USING (auth.role() = 'authenticated');

-- ═══════════════════════════════════════════════════════════════════════
-- DADOS INICIAIS — Mentores
-- (execute após criar as tabelas; ajuste os e-mails)
-- ═══════════════════════════════════════════════════════════════════════

INSERT INTO mentores (nome, email) VALUES
    ('Luan',      'luan.araujo@docente.senai-ce.org.br'),
    ('Raimundo',  'raimundo@docente.senai-ce.org.br'),
    ('Lucilani',  'lucilani@docente.senai-ce.org.br'),
    ('Décio',     'decio@docente.senai-ce.org.br'),
    ('Claudecir', 'claudecir@docente.senai-ce.org.br');
