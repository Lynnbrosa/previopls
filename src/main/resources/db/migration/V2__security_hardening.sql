-- Hardening de segurança:
--   1) audit_logs: trilha de auditoria para ações críticas
--   2) login_attempts: histórico de tentativas (lockout anti brute-force)
--   3) clientes.email/telefone passam a guardar ciphertext AES-GCM (TEXT)
--      Os valores existentes do V2 são INVALIDADOS pelo migrate — ver build_seed.py
--      que regenera V2 já criptografado.

CREATE TABLE audit_logs (
    id            UUID PRIMARY KEY,
    action        VARCHAR(40)  NOT NULL,
    actor_id      UUID,
    actor_email   VARCHAR(180),
    actor_role    VARCHAR(20),
    entity_type   VARCHAR(40),
    entity_id     VARCHAR(64),
    request_id    VARCHAR(36),
    remote_ip     VARCHAR(64),
    user_agent    VARCHAR(255),
    details       TEXT,
    occurred_at   TIMESTAMP    NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_audit_action CHECK (action IN (
        'LOGIN_SUCCESS', 'LOGIN_FAILED', 'LOGIN_LOCKED', 'LOGOUT',
        'CLIENTE_CREATED', 'LEAD_CREATED', 'LEAD_PATCHED',
        'UNAUTHORIZED_ACCESS', 'FORBIDDEN_ACCESS'
    ))
);
CREATE INDEX ix_audit_logs_occurred_at ON audit_logs (occurred_at DESC);
CREATE INDEX ix_audit_logs_actor_id    ON audit_logs (actor_id);
CREATE INDEX ix_audit_logs_action      ON audit_logs (action);
CREATE INDEX ix_audit_logs_entity      ON audit_logs (entity_type, entity_id);


CREATE TABLE login_attempts (
    id            UUID PRIMARY KEY,
    email         VARCHAR(180) NOT NULL,
    success       BOOLEAN      NOT NULL,
    remote_ip     VARCHAR(64),
    attempted_at  TIMESTAMP    NOT NULL DEFAULT NOW()
);
CREATE INDEX ix_login_attempts_email                ON login_attempts (email);
CREATE INDEX ix_login_attempts_attempted_at         ON login_attempts (attempted_at DESC);
CREATE INDEX ix_login_attempts_email_attempted_at   ON login_attempts (email, attempted_at DESC);


-- Email e telefone passam a guardar ciphertext (Base64 do IV+CT+TAG do AES-GCM).
-- O tipo TEXT acomoda os ~64 caracteres típicos do payload criptografado.
-- O CPF permanece em texto plano (busca por findByCpf depende de igualdade),
-- mas é sempre mascarado nas respostas via ClienteMapper.toResponse.
ALTER TABLE clientes ALTER COLUMN email TYPE TEXT;
ALTER TABLE clientes ALTER COLUMN telefone TYPE TEXT;

-- Política de retenção: campos para suportar soft delete + anonimização
-- programada. (Job @Scheduled pode aplicar quando data_retencao expirar.)
ALTER TABLE clientes ADD COLUMN IF NOT EXISTS retencao_ate TIMESTAMP;
COMMENT ON COLUMN clientes.retencao_ate IS 'LGPD: data limite para retenção; após isso PII deve ser anonimizada.';

-- Limpa dados do V2 — serão repopulados pelo build_seed.py regenerado,
-- desta vez com email e telefone já encriptados.
DELETE FROM leads;
DELETE FROM veiculos;
DELETE FROM clientes;
