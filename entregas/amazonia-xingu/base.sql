-- SQLite 3. Estrutura vazia; a preparação não importa detecções.
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS projeto (
    id TEXT PRIMARY KEY,
    versao INTEGER NOT NULL,
    configuracao_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS municipio (
    codigo_ibge TEXT PRIMARY KEY CHECK(length(codigo_ibge) = 7),
    nome TEXT NOT NULL,
    uf TEXT NOT NULL,
    versao_malha TEXT NOT NULL,
    geometria_analise_ref TEXT NOT NULL,
    geometria_video_ref TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS regiao (
    id TEXT PRIMARY KEY,
    nome TEXT NOT NULL,
    fonte_definicao TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS regiao_municipio (
    regiao_id TEXT NOT NULL REFERENCES regiao(id),
    codigo_ibge TEXT NOT NULL REFERENCES municipio(codigo_ibge),
    PRIMARY KEY(regiao_id, codigo_ibge)
);

-- Um snapshot deve ser fechado antes de exportar dados ao vídeo.
CREATE TABLE IF NOT EXISTS snapshot (
    id TEXT PRIMARY KEY,
    projeto_id TEXT NOT NULL REFERENCES projeto(id),
    criado_utc TEXT NOT NULL,
    corte_utc TEXT NOT NULL,
    sensor TEXT NOT NULL,
    fuso TEXT NOT NULL CHECK(fuso = 'UTC'),
    versao_malha TEXT NOT NULL,
    estado TEXT NOT NULL CHECK(estado IN ('preparando', 'validado', 'rejeitado')),
    manifesto_sha256 TEXT,
    CHECK(estado <> 'validado' OR manifesto_sha256 IS NOT NULL)
);
CREATE TABLE IF NOT EXISTS fonte (
    id INTEGER PRIMARY KEY,
    caminho TEXT NOT NULL,
    url TEXT NOT NULL,
    sha256 TEXT NOT NULL CHECK(length(sha256) = 64),
    bytes INTEGER NOT NULL CHECK(bytes >= 0),
    inventariado_utc TEXT NOT NULL,
    obtido_utc TEXT,
    last_modified TEXT,
    tipo TEXT NOT NULL CHECK(tipo IN ('anual_referencia', 'mensal', 'diario')),
    sensor_declarado TEXT,
    estado TEXT NOT NULL CHECK(estado IN ('inventariado', 'validado', 'rejeitado')),
    UNIQUE(caminho, sha256)
);
CREATE TABLE IF NOT EXISTS snapshot_fonte (
    snapshot_id TEXT NOT NULL REFERENCES snapshot(id),
    fonte_id INTEGER NOT NULL REFERENCES fonte(id),
    PRIMARY KEY(snapshot_id, fonte_id)
);
CREATE TABLE IF NOT EXISTS foco (
    snapshot_id TEXT NOT NULL REFERENCES snapshot(id),
    chave_deduplicacao TEXT NOT NULL,
    id_original TEXT,
    data_hora_utc TEXT NOT NULL,
    data_utc TEXT NOT NULL CHECK(length(data_utc) = 10),
    latitude REAL NOT NULL CHECK(latitude BETWEEN -90 AND 90),
    longitude REAL NOT NULL CHECK(longitude BETWEEN -180 AND 180),
    satelite TEXT NOT NULL,
    codigo_ibge TEXT NOT NULL REFERENCES municipio(codigo_ibge),
    PRIMARY KEY(snapshot_id, chave_deduplicacao)
);
CREATE INDEX IF NOT EXISTS foco_dia_municipio ON foco(snapshot_id, data_utc, codigo_ibge);
-- Preserva a linhagem quando a mesma observação aparece no mensal e no diário.
CREATE TABLE IF NOT EXISTS foco_fonte (
    snapshot_id TEXT NOT NULL,
    chave_deduplicacao TEXT NOT NULL,
    fonte_id INTEGER NOT NULL REFERENCES fonte(id),
    PRIMARY KEY(snapshot_id, chave_deduplicacao, fonte_id),
    FOREIGN KEY(snapshot_id, chave_deduplicacao) REFERENCES foco(snapshot_id, chave_deduplicacao),
    FOREIGN KEY(snapshot_id, fonte_id) REFERENCES snapshot_fonte(snapshot_id, fonte_id)
);
-- Estado referente à ingestão da fonte, não à ausência de nuvens/falhas do sensor.
CREATE TABLE IF NOT EXISTS cobertura_dia (
    snapshot_id TEXT NOT NULL REFERENCES snapshot(id),
    data_utc TEXT NOT NULL CHECK(length(data_utc) = 10),
    regiao_id TEXT NOT NULL REFERENCES regiao(id),
    estado TEXT NOT NULL CHECK(estado IN ('validado', 'parcial', 'ausente', 'nao_validado', 'futuro')),
    fim_coberto_utc TEXT,
    justificativa TEXT NOT NULL,
    PRIMARY KEY(snapshot_id, data_utc, regiao_id),
    CHECK(estado NOT IN ('validado', 'parcial') OR fim_coberto_utc IS NOT NULL)
);
CREATE TABLE IF NOT EXISTS cobertura_fonte (
    snapshot_id TEXT NOT NULL,
    data_utc TEXT NOT NULL,
    regiao_id TEXT NOT NULL,
    fonte_id INTEGER NOT NULL,
    PRIMARY KEY(snapshot_id, data_utc, regiao_id, fonte_id),
    FOREIGN KEY(snapshot_id, data_utc, regiao_id) REFERENCES cobertura_dia(snapshot_id, data_utc, regiao_id),
    FOREIGN KEY(snapshot_id, fonte_id) REFERENCES snapshot_fonte(snapshot_id, fonte_id)
);

-- A cobertura dirige a consulta: desconhecido permanece NULL, nunca vira zero.
CREATE VIEW IF NOT EXISTS diario_municipal AS
SELECT c.snapshot_id, c.data_utc, c.regiao_id, m.codigo_ibge, c.estado,
       CASE WHEN c.estado IN ('validado', 'parcial') THEN COUNT(f.chave_deduplicacao)
            ELSE NULL END AS focos
FROM cobertura_dia c
JOIN snapshot s ON s.id = c.snapshot_id
JOIN regiao_municipio m ON m.regiao_id = c.regiao_id
LEFT JOIN foco f ON f.snapshot_id = c.snapshot_id AND f.data_utc = c.data_utc
    AND f.codigo_ibge = m.codigo_ibge AND f.satelite = s.sensor
GROUP BY c.snapshot_id, c.data_utc, c.regiao_id, m.codigo_ibge, c.estado;

CREATE VIEW IF NOT EXISTS mensal_municipal AS
SELECT snapshot_id, substr(data_utc, 1, 7) AS mes_utc, regiao_id, codigo_ibge,
       SUM(focos) AS focos_observados,
       SUM(CASE WHEN estado = 'validado' THEN 1 ELSE 0 END) AS dias_validados,
       CAST(strftime('%d', date(substr(data_utc, 1, 7) || '-01', '+1 month', '-1 day')) AS INTEGER) AS dias_esperados,
       CASE WHEN SUM(CASE WHEN estado = 'validado' THEN 1 ELSE 0 END)
            = CAST(strftime('%d', date(substr(data_utc, 1, 7) || '-01', '+1 month', '-1 day')) AS INTEGER)
            THEN 'validado'
            WHEN SUM(CASE WHEN estado IN ('validado', 'parcial') THEN 1 ELSE 0 END) > 0
            THEN 'parcial' ELSE 'sem_dados' END AS estado
FROM diario_municipal
GROUP BY snapshot_id, substr(data_utc, 1, 7), regiao_id, codigo_ibge;

CREATE TABLE IF NOT EXISTS render (
    id TEXT PRIMARY KEY,
    snapshot_id TEXT NOT NULL REFERENCES snapshot(id),
    composicao TEXT NOT NULL,
    configuracao_sha256 TEXT NOT NULL,
    codigo_git TEXT NOT NULL,
    arquivo_mp4 TEXT NOT NULL,
    sha256_mp4 TEXT,
    fps INTEGER NOT NULL,
    frames INTEGER NOT NULL,
    estado TEXT NOT NULL CHECK(estado IN ('planejado', 'renderizado', 'aprovado', 'rejeitado')),
    relatorio_qa_ref TEXT
);
