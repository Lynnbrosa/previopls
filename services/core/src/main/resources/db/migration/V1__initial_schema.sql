-- PrevioPLS — esquema inicial
-- Entidades: usuarios, clientes, veiculos, leads

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE usuarios (
    id          UUID PRIMARY KEY,
    nome        VARCHAR(120)  NOT NULL,
    email       VARCHAR(180)  NOT NULL UNIQUE,
    senha_hash  VARCHAR(255)  NOT NULL,
    papel       VARCHAR(20)   NOT NULL,
    criado_em   TIMESTAMP     NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_usuarios_papel CHECK (papel IN ('ADMIN', 'CONSULTOR'))
);
CREATE INDEX ix_usuarios_email ON usuarios (email);


CREATE TABLE clientes (
    id               UUID PRIMARY KEY,
    nome             VARCHAR(180) NOT NULL,
    cpf              VARCHAR(14)  NOT NULL UNIQUE,
    email            VARCHAR(180),
    telefone         VARCHAR(20),
    regiao           VARCHAR(40)  NOT NULL,
    perfil           VARCHAR(20),
    score_risco      DOUBLE PRECISION,
    criado_em        TIMESTAMP    NOT NULL DEFAULT NOW(),
    classificado_em  TIMESTAMP,
    CONSTRAINT ck_clientes_perfil CHECK (perfil IS NULL OR perfil IN ('FIEL', 'ABANDONO', 'ESQUECIDO', 'ECONOMICO'))
);
CREATE INDEX ix_clientes_cpf ON clientes (cpf);
CREATE INDEX ix_clientes_perfil ON clientes (perfil);


CREATE TABLE veiculos (
    id                 UUID PRIMARY KEY,
    cliente_id         UUID           NOT NULL REFERENCES clientes(id) ON DELETE CASCADE,
    modelo             VARCHAR(80)    NOT NULL,
    versao             VARCHAR(80)    NOT NULL,
    ano                INTEGER        NOT NULL,
    vin                VARCHAR(17)    NOT NULL UNIQUE,
    data_compra        DATE           NOT NULL,
    valor_compra       NUMERIC(12, 2) NOT NULL,
    concessionaria_id  VARCHAR(40)    NOT NULL,
    criado_em          TIMESTAMP      NOT NULL DEFAULT NOW()
);
CREATE INDEX ix_veiculos_cliente_id ON veiculos (cliente_id);
CREATE INDEX ix_veiculos_vin ON veiculos (vin);
CREATE INDEX ix_veiculos_concessionaria_id ON veiculos (concessionaria_id);


CREATE TABLE leads (
    id              UUID PRIMARY KEY,
    cliente_id      UUID             NOT NULL REFERENCES clientes(id) ON DELETE CASCADE,
    veiculo_id      UUID             NOT NULL REFERENCES veiculos(id) ON DELETE CASCADE,
    score_risco     DOUBLE PRECISION NOT NULL,
    prioridade      VARCHAR(20)      NOT NULL,
    status          VARCHAR(20)      NOT NULL DEFAULT 'ABERTO',
    script_oferta   TEXT,
    observacao      TEXT,
    criado_em       TIMESTAMP        NOT NULL DEFAULT NOW(),
    atualizado_em   TIMESTAMP        NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_leads_prioridade CHECK (prioridade IN ('CRITICA', 'ALTA', 'MEDIA', 'BAIXA')),
    CONSTRAINT ck_leads_status     CHECK (status IN ('ABERTO', 'AGENDADO', 'RECUSADO', 'SEM_CONTATO'))
);
CREATE INDEX ix_leads_cliente_id        ON leads (cliente_id);
CREATE INDEX ix_leads_veiculo_id        ON leads (veiculo_id);
CREATE INDEX ix_leads_prioridade        ON leads (prioridade);
CREATE INDEX ix_leads_status            ON leads (status);
CREATE INDEX ix_leads_prioridade_status ON leads (prioridade, status);
