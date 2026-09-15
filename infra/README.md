# infra

Orquestração local e specs de deploy do PrevioPLS.

## Subir a stack completa

```bash
docker compose -f infra/docker-compose.yml up --build
```

Não há passos manuais. No primeiro boot:

- `certgen` gera um certificado TLS self-signed no volume `nginx_certs` (só uma vez; aceite o aviso do navegador em dev).
- `core` aplica as migrations Flyway (`V1` schema, `V2` hardening, `V3` seed com 300 clientes / 93 leads) e cria `admin@ford.com` e `consultor@ford.com`.
- `gateway` espera o banco, aplica as migrations Alembic, gera o par RSA de desenvolvimento no volume `gateway_keys` e cria `admin@ford.com`, `consultor@ford.com` e `analista@ford.com`.
- `ml-api` já vem com um modelo padrão gerado no build da imagem (validado contra features pós-venda no boot).

Para trocar os segredos de desenvolvimento: `cp infra/.env.example infra/.env` e edite. Os defaults do compose bastam para a demo local; nunca use-os fora da sua máquina.

Portas no host: `80` e `443` (nginx) e `127.0.0.1:5000` (Core, apenas para o app mobile em dev; `CORE_HOST_PORT` troca a porta, útil no macOS onde a 5000 é do AirPlay Receiver; remova `ports` do serviço `core` se não precisar). Os demais serviços ficam restritos à rede interna `previopls`.

Erros gerados pelo próprio nginx em `/api/*` (429 do rate limit, 502/503/504 com upstream fora) saem em JSON no contrato `{error:{code,message}}`. O header HSTS só é enviado para hosts diferentes de `localhost`/`127.*`, para não forçar HTTPS em outros servidores locais durante o desenvolvimento.

## Rotas no nginx

| Caminho público                  | Destino                             | Observação                              |
|----------------------------------|-------------------------------------|------------------------------------------|
| `https://localhost/api/v1/*`     | Gateway FastAPI (remove o `/api`)   | `/api/v1/auth/login` limitado a 5 req/min |
| `https://localhost/api/health`   | Gateway `/health`                   | reporta `database` e `core`              |
| `https://localhost/api/docs`     | Gateway `/docs` (Swagger)           | apenas em dev (`APP_ENV != production`)  |
| `https://localhost/api/*` (demais) | Admin Web Next.js                 | route handlers da sessão do painel: `/api/auth/login`, `/api/auth/logout`, `/api/leads/{id}` |
| `https://localhost/*`            | Admin Web Next.js                   |                                          |

Só o que está sob `/api/v1/` (mais `/api/health`, `/api/docs`, `/api/openapi.json`) vai para o Gateway. As outras rotas `/api/*` são do próprio Next.js: o navegador fala com o painel, e o painel fala com o Gateway pela rede interna. Um `location /api/` genérico apontando para o Gateway faz o login do painel responder 404 e o formulário mostrar "Credenciais inválidas".

O admin-web fala com o Gateway pela rede interna (`INTERNAL_GATEWAY_URL=http://gateway:8000`). O Gateway autentica (JWT RS256) e repassa ao Core com um JWT interno HS256 (ADR-001/ADR-003). O app mobile do consultor conecta direto no Core via `EXPO_PUBLIC_API_URL` (ver [`apps/consultor-mobile/README.md`](../apps/consultor-mobile/README.md)).

## Bancos de dados

Um único `postgres:16-alpine` hospeda duas bases criadas pelo [`init.sql`](postgres/init.sql):

- `previopls_core`: usado pelo Core (Flyway).
- `previopls_gateway`: usado pelo Gateway (Alembic). No modo proxy guarda apenas usuários, refresh tokens, tentativas de login e `audit_logs`; as tabelas de domínio existem para o modo standalone.

A separação física por database evita colisão de nomes de tabelas e permite migrar para clusters distintos sem refatoração (ver [`ARCHITECTURE.md`](../ARCHITECTURE.md), ADR-001).

## Variáveis compartilhadas

| Variável              | Quem usa            | Para quê                                                        |
|-----------------------|---------------------|-----------------------------------------------------------------|
| `JWT_SECRET`          | core, gateway       | HS256: o Core valida os tokens que ele mesmo emite e os tokens internos que o Gateway assina por requisição |
| `BOOTSTRAP_ADMIN_EMAIL`, `BOOTSTRAP_ADMIN_PASSWORD` | gateway | primeiro administrador em produção (em dev o seed de demo já cria `admin@ford.com`) |
| `APP_CRYPTO_KEY`      | core, build_seed.py | AES-256-GCM da PII em repouso. O seed `V3` foi cifrado com a chave dev; ao trocar, regenere o seed |
| `HMAC_PAYLOAD_SECRET` | gateway, faturamento| assinatura `X-Signature` do `POST /api/v1/clientes`             |
| `FERNET_KEY`, `CPF_HASH_PEPPER` | gateway   | criptografia e lookup de PII no modo standalone                 |
| `POSTGRES_PASSWORD`   | postgres, core, gateway | senha do usuário `previopls`                                |

## Healthchecks e ordem de boot

O `depends_on` com `condition` garante a ordem:

1. `postgres` (espera `pg_isready`) e `certgen` (termina com sucesso).
2. `ml-api` (espera 200 em `/health`).
3. `core` (após postgres + ml-api; `start_period` de 40 s para a JVM).
4. `gateway` (após postgres + core; `/health` só fica `ok` com banco e core `up`).
5. `admin-web` (após gateway saudável; healthcheck em `/login`).
6. `nginx` (após certgen, gateway e admin-web saudáveis).

## Dockerfiles

- `services/gateway/Dockerfile`: entrypoint espera o banco, roda `alembic upgrade head` e sobe o uvicorn. Diretório `/app/keys` pertence ao usuário `app` para o volume de chaves.
- `services/ml/api/Dockerfile`: gera `models/ml_model.pkl` sintético no build se não houver um pkl real na pasta.
- `services/core/Dockerfile`: build multi-stage Maven + JRE 21, `MaxRAMPercentage=75`.
- `apps/admin-web/Dockerfile`: Next.js `output: standalone` (`node server.js`).

## Rodar sem Docker

Útil para depurar um serviço de cada vez. Requer Postgres 16, JDK 21 + Maven, Python 3.11+ e Node 20.

```bash
# 1) bancos
psql -U postgres -f infra/postgres/init.sql       # cria previopls_core e previopls_gateway (owner previopls)

# 2) ml-api (porta 8000)
cd services/ml/api && pip install -r requirements.txt && python -m app.build_default_model
uvicorn app.main:app --port 8000

# 3) core (porta 5000)
cd services/core
DATABASE_URL=jdbc:postgresql://localhost:5432/previopls_core DB_USERNAME=previopls DB_PASSWORD=previopls \
ML_API_URL=http://localhost:8000 JWT_SECRET=dev-only-change-me-this-key-must-be-at-least-32-bytes-long \
mvn spring-boot:run

# 4) gateway em modo proxy (porta 8001; o entrypoint aplica as migrations)
cd services/gateway && pip install -r requirements.txt
APP_ENV=development PORT=8001 \
DATABASE_URL=postgresql+psycopg://previopls:previopls@localhost:5432/previopls_gateway \
FERNET_KEY=$(python scripts/gen_fernet_key.py) CPF_HASH_PEPPER=dev-pepper-com-pelo-menos-32-bytes-aaaa \
HMAC_PAYLOAD_SECRET=dev-hmac-com-pelo-menos-32-bytes-aaaaaaaa \
CORE_API_URL=http://localhost:5000 JWT_SECRET=dev-only-change-me-this-key-must-be-at-least-32-bytes-long \
./docker-entrypoint.sh

# 5) admin-web (porta 3000)
cd apps/admin-web && npm install
INTERNAL_GATEWAY_URL=http://localhost:8001 npm run dev
```

Fluxo de fumaça (login pelo Gateway, lista de leads vinda do Core):

```bash
TOKEN=$(curl -s -X POST localhost:8001/v1/auth/login -H 'Content-Type: application/json' \
  -d '{"email":"consultor@ford.com","senha":"cons123"}' | python -c 'import sys,json;print(json.load(sys.stdin)["access_token"])')
curl -s -H "Authorization: Bearer $TOKEN" 'localhost:8001/v1/leads?status=aberto&per_page=3'
```

## Problemas comuns

| Sintoma | Causa | O que fazer |
|---|---|---|
| Login do painel mostra "O servidor respondeu HTTP 404" ou "Credenciais inválidas" | nginx antigo mandando `/api/auth/login` ao Gateway | `git pull` e `docker compose up --build` (recria nginx e admin-web) |
| Gateway em crash loop com `database "previopls_gateway" does not exist` | volume `pgdata` criado antes do `init.sql` (por exemplo pelo compose antigo do Gateway) | `docker compose -f infra/docker-compose.yml down -v` e subir de novo (apaga os dados locais) |
| `docker compose up` falha com porta 5000 em uso (macOS) | AirPlay Receiver usa a 5000 | `CORE_HOST_PORT=5001` no `infra/.env` |
| Login correto responde 401 | 5 falhas nos últimos 15 min para aquele e-mail (lockout) ou 6+ logins no mesmo minuto pelo mesmo IP (429) | aguardar; o lockout expira sozinho |
| Gateway em produção sem nenhum usuário | `SEED_DEFAULT_USERS` desligado e `BOOTSTRAP_ADMIN_*` não definidos | definir `BOOTSTRAP_ADMIN_EMAIL` / `BOOTSTRAP_ADMIN_PASSWORD` ou `python -m app.db.seed` no shell do container |
| `http://localhost:3000` ou `:5000` redireciona sozinho para https | HSTS gravado no navegador para `localhost` por uma versão antiga do nginx | remover `localhost` em `chrome://net-internals/#hsts` (Chrome) ou limpar dados do site (Firefox); a versão atual não envia HSTS para localhost |

## Deploy para piloto

A pasta [`deploy/`](deploy/) contém as specs por provedor: Vercel para o admin-web, Render para os 3 backends, Neon para o Postgres. Stack escolhida por priorizar free tier sem cartão amarrado. Não há comando de deploy automatizado; o deploy é manual.
