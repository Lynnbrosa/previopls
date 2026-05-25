# infra

Orquestração local e specs de deploy do PrevioPLS.

## Subir a stack completa

```bash
# A partir da raiz do monorepo, gerar segredos do Gateway uma única vez:
cd services/gateway
chmod +x scripts/*.sh
./scripts/gen_rsa_keys.sh           # keys/jwt_private.pem + keys/jwt_public.pem
./scripts/gen_self_signed_cert.sh   # nginx/certs/dev.{crt,key}
python scripts/gen_fernet_key.py    # imprime a FERNET_KEY (copie para infra/.env)

cd ../../infra
cp .env.example .env                # opcional: ajustar segredos
docker compose up --build
```

A stack expõe apenas o nginx em `80` e `443`. As demais portas (`5000` core, `8000` gateway, `8000` ml-api, `3000` admin-web) ficam restritas à rede interna `previopls`.

## Rotas no nginx

| Caminho público                  | Destino                       |
|----------------------------------|-------------------------------|
| `https://localhost/api/v1/*`     | Gateway FastAPI (strip `/api`)|
| `https://localhost/api/health`   | Gateway `/health`             |
| `https://localhost/*`            | Admin Web Next.js             |

O app mobile do consultor não passa pelo nginx no compose local; ele conecta direto no Core via `EXPO_PUBLIC_API_URL` (ver [`apps/consultor-mobile/README.md`](../apps/consultor-mobile/README.md)).

## Bancos de dados

Um único `postgres:16-alpine` hospeda duas bases criadas pelo [`init.sql`](postgres/init.sql):

- `previopls_core`: usado pelo Core (Flyway aplica `V1__initial_schema.sql`, `V2__security_hardening.sql`, `V3__seed_real_data.sql`).
- `previopls_gateway`: usado pelo Gateway (Alembic gerencia o schema).

Os schemas são parecidos por desenho, ver [`ARCHITECTURE.md`](../ARCHITECTURE.md) seção 6 (ADR-001). A separação física por database evita colisão de nomes de tabelas e permite migrar para clusters distintos sem refatoração.

## Dockerfiles

- `services/gateway/Dockerfile`: usado tal qual está no subtree.
- `services/ml/api/Dockerfile`: criado na Fase 4 (este monorepo).
- `services/core/Dockerfile`: build multi-stage Maven + JRE 21. Adicionado ao serviço Core para que o compose e plataformas de deploy (Render, Vercel) detectem automaticamente.
- `apps/admin-web/Dockerfile`: criado na Fase 5 (Next.js standalone).

## Healthchecks e ordem de boot

O `depends_on` com `condition: service_healthy` garante a ordem:

1. `postgres` (espera `pg_isready`).
2. `ml-api` (espera resposta 200 em `/health`).
3. `core` (espera após postgres + ml-api).
4. `gateway` (espera após postgres + core).
5. `admin-web` (espera gateway saudável).
6. `nginx` (sobe assim que gateway e admin-web estão prontos).

## Subir um serviço isolado

Cada serviço continua tendo seu próprio fluxo. Veja os READMEs:

- [`services/gateway/README.md`](../services/gateway/README.md): `docker compose up` interno.
- [`services/core/README.md`](../services/core/README.md): `mvn spring-boot:run`.
- [`services/ml/notebook/README.md`](../services/ml/notebook/README.md): `jupyter notebook`.
- [`apps/consultor-mobile/README.md`](../apps/consultor-mobile/README.md): `npm start`.

## Deploy para piloto

A pasta [`deploy/`](deploy/) contém as specs por provedor: Vercel para o admin-web, Render para os 3 backends, Neon para o Postgres. Stack escolhida por priorizar free tier sem cartão amarrado. Não há comando de deploy automatizado; o deploy é manual.
