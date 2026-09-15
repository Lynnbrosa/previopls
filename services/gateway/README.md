# PrevioPLS Security API (Gateway)

Borda de segurança LGPD do PrevioPLS. Backend Python (**FastAPI · SQLAlchemy 2 · Pydantic v2 · PostgreSQL · Alembic · structlog · slowapi · cryptography (Fernet + RS256) · nginx TLS reverso**), nascido na disciplina de Cybersecurity da challenge FIAP 2026 e hoje o único serviço exposto publicamente no monorepo.

> Ford é o **controlador** dos dados; este sistema atua como **operador** (LGPD Art. 5º, VIII).
> Threat model STRIDE completo em [`docs/threat-model.md`](../../docs/threat-model.md).

## Dois modos de operação

| Modo | Quando | O que acontece com `/v1/clientes` e `/v1/leads*` |
|---|---|---|
| **Proxy para o Core** (padrão do monorepo) | `CORE_API_URL` definido (ex.: `http://core:5000`) | O Gateway valida borda (TLS via nginx, JWT RS256, RBAC, HMAC, schema, rate limit), registra auditoria e repassa ao Core com um **JWT interno HS256** de 60 s assinado com `JWT_SECRET` (o mesmo do Core). A resposta do Core (contrato camelCase) é devolvida tal qual. Ver ADR-001/ADR-003 em [`ARCHITECTURE.md`](../../ARCHITECTURE.md). |
| **Standalone** (repositório original da challenge) | `CORE_API_URL` vazio | O Gateway persiste cliente/veículo/lead no próprio banco, com PII em Fernet e classificação pelo stub determinístico. Contrato snake_case documentado no `/docs`. |

Em ambos os modos a autenticação (`/v1/auth/*`), a auditoria (`/v1/admin/audit-log`) e o `/v1/llm-assist` são do próprio Gateway. Headers `X-Request-Id` e `X-Forwarded-For` são propagados ao Core para correlacionar as duas trilhas de auditoria.

**Repositórios irmãos da challenge:**
[`challenge-SOA`](https://github.com/Lynnbrosa/challenge-SOA) (backend Java/Spring Boot, mesmo domínio de negócio) ·
[`challenge-Mobile`](https://github.com/Lynnbrosa/challenge-Mobile) (app React Native do consultor) ·
[`challenge-IAML`](https://github.com/Lynnbrosa/challenge-IAML) (notebook IA/ML + gerador de seed)

## Estrutura

```
PrevioPLS-Security/
├── app/
│   ├── main.py                    FastAPI factory + meta endpoints
│   ├── core/
│   │   ├── config.py              Pydantic Settings (env-based)
│   │   ├── security.py            JWT RS256 + bcrypt + RBAC dependency
│   │   ├── crypto.py              Fernet + CPF hash + pseudonimização + masking
│   │   ├── hmac_signing.py        Verificação HMAC em payloads críticos
│   │   ├── logging.py             structlog JSON + PII masking processor
│   │   ├── errors.py              Exception handlers globais (sem stack trace)
│   │   ├── middleware.py          Request ID + Security headers
│   │   └── ratelimit.py           slowapi limiter
│   ├── api/v1/
│   │   ├── auth.py                POST /login /refresh /logout
│   │   ├── clientes.py            POST /clientes (Admin + HMAC obrigatório) → Core ou local
│   │   ├── leads.py               GET list / GET id / PATCH (Consultor+) → Core ou local
│   │   └── audit.py               GET /admin/audit-log (Admin/Analista)
│   ├── services/                  Lógica de negócio + auditoria
│   │   └── core_client.py         Cliente HTTP do Core (JWT interno HS256, correlação, 503)
│   ├── schemas/                   DTOs Pydantic v2 (extra='forbid')
│   ├── models/                    SQLAlchemy ORM
│   └── db/
│       ├── session.py
│       └── seed.py                Usuários padrão (dev/demo)
├── alembic/                       Migrações (aplicadas no boot pelo entrypoint)
├── docker-entrypoint.sh           Espera o banco → alembic upgrade head → uvicorn
├── nginx/
│   ├── nginx.conf                 TLS 1.2+, HSTS, rate limit, security headers
│   └── certs/                     Gerados por scripts/gen_self_signed_cert.sh
├── scripts/
│   ├── gen_rsa_keys.sh            RSA 2048 para JWT
│   ├── gen_self_signed_cert.sh    TLS dev
│   └── gen_fernet_key.py          Chave Fernet
├── tests/
│   ├── test_security.py           Fernet roundtrip, JWT, HMAC, PII masking
│   └── test_core_proxy.py         Tradução de contrato, JWT interno, 503, headers de correlação
├── docker-compose.yml             db + api + nginx
├── Dockerfile
├── requirements.txt
├── pyproject.toml
└── .env.example
```

## Controles por domínio (mapeamento da rubrica 100 pts)

### 1. Validação de Entrada (20 pts)

| Item | Onde |
|---|---|
| Pydantic v2 com `extra="forbid"` em todos os DTOs | [`app/schemas/`](app/schemas/) |
| Anti SQLi: SQLAlchemy parametriza, Enum tipado em filtros | [`app/services/lead_service.py`](app/services/lead_service.py) |
| Regex estrito: CPF `^\d{11}$`, VIN `^[A-HJ-NPR-Z0-9]{17}$`, placa Mercosul | [`app/schemas/cliente.py`](app/schemas/cliente.py) |
| Sanitização anti-XSS em campo livre `observacao` | [`app/services/lead_service.py`](app/services/lead_service.py) |
| Limites de tamanho: body 1MB (nginx), strings com `max_length` | `nginx.conf` + Pydantic |
| Handler global JSON sem stack trace | [`app/core/errors.py`](app/core/errors.py) |

### 2. Auth & Authz (20 pts)

| Item | Onde |
|---|---|
| JWT **RS256** assimétrico (chaves em `keys/`) | [`app/core/security.py`](app/core/security.py) |
| Access 15 min + refresh 7 dias com rotação + denylist | [`app/services/auth_service.py`](app/services/auth_service.py) + `refresh_tokens` |
| Claim `type` explícita (access vs refresh) impede troca | `decode_token(expected_type=...)` |
| bcrypt cost 12 | `hash_password` em `security.py` |
| RBAC `Consultor / Admin / Analista` via `Depends(requires_role(Role.ADMIN, ...))`; sem token → 401 `WWW-Authenticate: Bearer`; papel errado → 403 + `FORBIDDEN_ACCESS` no audit | [`app/core/security.py`](app/core/security.py) |
| Lockout: 5 falhas/60s → 15 min de bloqueio | [`app/services/lockout_service.py`](app/services/lockout_service.py) |

### 3. Proteção de APIs (20 pts)

| Item | Onde |
|---|---|
| HTTPS + HSTS preload (TLS 1.2/1.3, ciphers fortes) | [`nginx/nginx.conf`](nginx/nginx.conf) |
| Rate limit nível nginx + slowapi (defesa em profundidade) | nginx `limit_req_zone` + `app/core/ratelimit.py` |
| 100 req/min global · 5 req/min em /login | `.env` + `nginx.conf` |
| CORS whitelist explícita (origins de prod) | `app/main.py` |
| Headers OWASP baseline (HSTS, CSP, X-Frame, etc) duplicados em nginx + middleware | `nginx.conf` + `app/core/middleware.py` |
| HMAC-SHA256 em `POST /v1/clientes` com `X-Signature` + `X-Timestamp` (janela 5 min) | [`app/core/hmac_signing.py`](app/core/hmac_signing.py) |

### 4. Dados e Privacidade (25 pts)

| Item | Onde |
|---|---|
| CPF cifrado com **Fernet** (não-determinístico) + `cpf_hash` HMAC pra lookup | [`app/core/crypto.py`](app/core/crypto.py) + [`app/models/cliente.py`](app/models/cliente.py) |
| Email + telefone também cifrados (Fernet) | mesmo |
| Mascaramento em DTOs: `mask_cpf`, `mask_email`, `mask_telefone` — plaintext nunca sai por response | `cliente_to_output` |
| Pseudonimização irreversível (`pseudo_<sha256-truncado>`) pra ML e dashboards | `pseudonymize()` |
| Retenção LGPD 5 anos → anonimização irreversível agendada | [`app/services/retention_service.py`](app/services/retention_service.py) |
| PII masking nos logs (CPF, email, Bearer, dígitos longos) | `pii_masking_processor` no structlog |

### 5. Logs e Auditoria (15 pts)

| Item | Onde |
|---|---|
| structlog **JSON** com `request_id` correlacionando todos os logs | [`app/core/logging.py`](app/core/logging.py) + `middleware.py` |
| Tabela `audit_logs` (quem, o quê, quando, IP, UA, request_id, details) | [`app/models/audit_log.py`](app/models/audit_log.py) |
| 13 ações cobertas (LOGIN_SUCCESS/FAILED/LOCKED, CLIENTE_*, LEAD_*, UNAUTHORIZED_ACCESS, FORBIDDEN_ACCESS, SIGNATURE_REJECTED, MASS_QUERY_DETECTED) | [`app/models/audit_log.py`](app/models/audit_log.py) |
| Alertas: 5 falhas login/1min, consulta massiva (>100 leads/min), alteração de perfil | [`app/services/alert_service.py`](app/services/alert_service.py) |
| Webhook opcional pra SIEM/Slack/PagerDuty | `SECURITY_ALERT_WEBHOOK_URL` |
| Endpoint admin pra consulta da trilha | `GET /v1/admin/audit-log` |

## Setup completo

### No monorepo (recomendado)

```bash
docker compose -f infra/docker-compose.yml up --build
```

O Gateway sobe em modo proxy, aplica as migrations, gera o par RSA de dev no volume `gateway_keys` e cria os usuários padrão. API em `https://localhost/api/v1/...`, Swagger em `https://localhost/api/docs`. Ver [`infra/README.md`](../../infra/README.md).

### Isolado (standalone, como no repositório original)

```bash
cp .env.example .env               # deixe CORE_API_URL vazio para o modo standalone
docker compose up --build          # db + api + nginx deste diretório; migrations rodam no boot
```

A API fica em `https://localhost/health` e `https://localhost/docs`. Aceite o warning de cert self-signed (gere com `scripts/gen_self_signed_cert.sh`).

### Sem container

```bash
pip install -r requirements.txt
export DATABASE_URL=postgresql+psycopg://previopls:previopls@localhost:5432/previopls_gateway
export FERNET_KEY=$(python scripts/gen_fernet_key.py) CPF_HASH_PEPPER=... HMAC_PAYLOAD_SECRET=...
export CORE_API_URL=http://localhost:5000 JWT_SECRET=<mesmo-do-core>   # ou omita para standalone
./docker-entrypoint.sh             # migrations + uvicorn em :8000 (PORT para trocar)
```

### Variáveis específicas do Gateway

| Var | Default | Descrição |
|---|---|---|
| `CORE_API_URL` | vazio | URL interna do Core. Definida = modo proxy. |
| `JWT_SECRET` | vazio | Segredo HS256 compartilhado com o Core; obrigatório no modo proxy. |
| `CORE_TIMEOUT_SECONDS` | `5` | Timeout das chamadas ao Core (connect 2 s). Falha → `503 CORE_UNAVAILABLE`. |
| `ROOT_PATH` | vazio | Prefixo público removido pelo proxy reverso (`/api` no compose). Só afeta `/docs`. |
| `SEED_DEFAULT_USERS` | `true` fora de produção | Cria `admin@ford.com/admin123`, `consultor@ford.com/cons123`, `analista@ford.com/analista123`. |
| `JWT_AUTO_GENERATE_KEYS` | `true` fora de produção | Gera o par RSA se os arquivos não existirem. Em produção a ausência falha o boot. |
| `APP_ENV` | `development` | `production` desliga `/docs` e os defaults de dev acima. |

### Testar end-to-end (compose do monorepo)

```bash
# Sem JWT: 401
curl -k https://localhost/api/v1/leads

# Login (rate limit 5/min por IP)
curl -k -X POST https://localhost/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"consultor@ford.com","senha":"cons123"}'

# Leads vindos do Core (contrato camelCase do Core, com perfil e prioridade em minúsculo)
curl -k -H "Authorization: Bearer <ACCESS_TOKEN>" 'https://localhost/api/v1/leads?status=aberto&prioridade=critica'

# POST /clientes EXIGE HMAC + papel admin. Exemplo de assinatura em bash:
BODY='{"nome":"Maria","cpf":"12345678900","regiao":"SP","veiculo":{"modelo":"Ranger","versao":"XLT","ano":2026,"vin":"9BFZZZ8F7NB000001","data_compra":"2026-05-13","valor_compra":"250000.00","concessionaria_id":"FORD-SP-001"}}'
TS=$(date +%s)
SIG=$(printf '%s.%s' "$TS" "$BODY" | openssl dgst -sha256 -hmac "$HMAC_PAYLOAD_SECRET" | awk '{print $2}')
curl -k -X POST https://localhost/api/v1/clientes \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ACCESS_TOKEN_ADMIN>" \
  -H "X-Timestamp: $TS" \
  -H "X-Signature: $SIG" \
  -d "$BODY"
# → 201 com a resposta do Core (cliente com PII mascarada, perfil, scoreRisco, leadId quando o perfil gera lead)
```

No modo standalone, remova o prefixo `/api` das URLs acima.

### Anonimização agendada (LGPD retention, modo standalone)

Não é cron automático ainda — rode manualmente ou agende no host:

```bash
docker compose exec api python -c "from app.db.session import session_scope; from app.services.retention_service import anonymize_expired
with session_scope() as s: print(anonymize_expired(s))"
```

No modo proxy a PII de clientes vive no Core; a retenção passa a ser aplicada lá (`clientes.retencao_ate`).

## Testes

```bash
pip install -r requirements.txt pytest
pytest -v
```

Os testes não precisam de banco:

- `tests/test_security.py`: Fernet round-trip, CPF hash determinístico, mascaramento de PII (CPF/email/telefone), JWT RS256 sign/verify + rejeição de tipo incorreto + tampering, HMAC constant-time, PII masking nos logs.
- `tests/test_core_proxy.py`: tradução snake_case → camelCase para o Core, JWT interno HS256 (segredo compartilhado, TTL curto, distinto do RS256 externo), propagação de `X-Request-Id`/`X-Forwarded-For`, mapeamento de falha de rede para `503 CORE_UNAVAILABLE`, repasse de erros do Core, geração automática do par RSA em dev.

O workflow de CI do monorepo roda esta suíte em cada push.

## Comandos úteis

```bash
# Nova migration a partir do diff dos models
docker compose exec api alembic revision --autogenerate -m "descricao"

# Aplicar (o entrypoint já faz isso no boot)
docker compose exec api alembic upgrade head

# Voltar uma
docker compose exec api alembic downgrade -1

# Tail de logs estruturados
docker compose logs -f api | jq

# Trilha de auditoria (eventos de segurança nas últimas 24h)
docker compose exec db psql -U previopls -c "
  SELECT action, count(*) FROM audit_logs
  WHERE occurred_at > NOW() - INTERVAL '24 hours'
  GROUP BY action ORDER BY count DESC;
"
```

## Quê tá pronto pra produção (e o que não tá)

| Pronto | Falta |
|--------|-------|
| TLS + HSTS + CSP + headers OWASP | Cert válido (Let's Encrypt) |
| JWT RS256 com rotação de refresh + denylist | Chave privada em KMS/HSM (hoje em arquivo) |
| Fernet em CPF/email/telefone | Rotação de chave (Fernet `MultiFernet`) |
| Rate limit em 2 camadas (nginx + slowapi) | Redis backend pra rate limit distribuído |
| Audit log + alertas in-process | Integração com SIEM externo |
| Anonimização irreversível 5 anos | Agendador automático (cron/celery) |
| Logs JSON com masking de PII | Coletor central (Loki/CloudWatch) |
| HMAC obrigatório em rota crítica | Rotação programada da chave HMAC |
| Migrations no boot + chaves RSA de dev automáticas | Chaves de produção via KMS/Secret Files (nunca geradas no container) |
| Proxy para o Core com JWT interno de 60 s | mTLS entre gateway e core na rede privada |

Detalhamento completo dos riscos residuais em [`docs/threat-model.md`](../../docs/threat-model.md).
