# Render · gateway

Edge de segurança LGPD do PrevioPLS. Único serviço Render exposto publicamente.

## Setup no painel da Render

1. **New** → **Web Service**.
2. **Connect a repository**: `Lynnbrosa/previopls`.
3. **Name**: `previopls-gateway`.
4. **Root Directory**: `services/gateway`.
5. **Runtime**: `Docker`. Dockerfile do próprio diretório.
6. **Plan**: Free (suspende após 15 min de inatividade, acorda em 30 a 60 s no primeiro request).
7. **Health Check Path**: `/health`.
8. **Auto-Deploy**: `Yes` (apenas se o branch for `main`).

## Variáveis de ambiente

| Var                     | Valor                                                                 |
|-------------------------|------------------------------------------------------------------------|
| `APP_ENV`               | `production` (desliga `/docs`, exige chaves RSA presentes, não cria usuários seed) |
| `DATABASE_URL`          | `postgresql+psycopg://<user>:<pass>@<neon-host>/previopls_gateway?sslmode=require` (a string `postgresql://` copiada do Neon também é aceita) |
| `CORE_API_URL`          | URL interna do core na Render (`https://previopls-core.onrender.com`) — ativa o modo proxy |
| `JWT_SECRET`            | o mesmo segredo HS256 configurado no core (assina o JWT interno por requisição) |
| `SEED_DEFAULT_USERS`    | `false` (`true` só em demo: cria admin@ford.com/admin123 etc.)       |
| `BOOTSTRAP_ADMIN_EMAIL` | e-mail do primeiro administrador (criado no boot se não existir)      |
| `BOOTSTRAP_ADMIN_PASSWORD` | senha inicial do primeiro administrador (só aplicada na criação)   |
| `JWT_AUTO_GENERATE_KEYS`| `false` (chaves vêm de Secret Files)                                  |
| `FERNET_KEY`            | gerado uma vez, mesmo valor em todos os ambientes                     |
| `CPF_HASH_PEPPER`       | 32 bytes aleatórios                                                   |
| `HMAC_PAYLOAD_SECRET`   | 32 bytes aleatórios                                                   |
| `JWT_PRIVATE_KEY_PATH`  | `/app/keys/jwt_private.pem`                                          |
| `JWT_PUBLIC_KEY_PATH`   | `/app/keys/jwt_public.pem`                                           |
| `LOG_LEVEL`             | `INFO`                                                                |

As chaves RSA do JWT precisam ser materializadas no container. No piloto, gere com `services/gateway/scripts/gen_rsa_keys.sh` e suba via Render Secret Files (Settings → Secret Files), mountando em `/app/keys/jwt_private.pem` e `/app/keys/jwt_public.pem`. Em produção, mova para KMS gerenciado.

## Domínio público

`api.previopls.com.br`. Settings → Custom Domains. Render gera o certificado TLS via Let's Encrypt.

## Migrations e boot

O entrypoint do container espera o banco, roda `alembic upgrade head` e só então sobe o uvicorn. Não há passo manual de migration. Em produção o boot falha se as chaves RSA não estiverem montadas (nenhuma chave é gerada automaticamente com `APP_ENV=production`).

## Usuários

O Gateway não tem endpoint de gestão de usuários. Sem `SEED_DEFAULT_USERS=true` e sem `BOOTSTRAP_ADMIN_*`, um Gateway novo em produção não tem nenhum usuário e todo login responde 401 ("Credenciais inválidas" no painel). Defina `BOOTSTRAP_ADMIN_EMAIL` e `BOOTSTRAP_ADMIN_PASSWORD` antes do primeiro deploy. Para criar consultores e analistas, use o shell do serviço na Render:

```bash
GATEWAY_USER_PASSWORD='senha-forte' python -m app.db.seed --email consultor@concessionaria.com.br --papel consultor --nome "Nome"
```

## Health check

O Dockerfile do gateway já define `HEALTHCHECK` (curl em `/health`). Render usa o mesmo path por configuração. O corpo reporta `components.database` e `components.core`.

## Limitações do plano free

- Suspende após 15 min sem tráfego. Primeiro request acorda o container.
- 750 horas-mês de runtime gratuito (suficiente se for o único serviço público).
- 100 GB de bandwidth gratuito.
- Não usar para produção continuada. Migre para Starter ($7/mês) para uptime contínuo.
