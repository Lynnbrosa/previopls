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
| `APP_ENV`               | `production`                                                          |
| `DATABASE_URL`          | `postgresql+psycopg://<user>:<pass>@<neon-host>/previopls_gateway?sslmode=require` |
| `FERNET_KEY`            | gerado uma vez, mesmo valor em todos os ambientes                     |
| `CPF_HASH_PEPPER`       | 32 bytes aleatórios                                                   |
| `HMAC_PAYLOAD_SECRET`   | 32 bytes aleatórios                                                   |
| `JWT_PRIVATE_KEY_PATH`  | `/app/keys/jwt_private.pem`                                          |
| `JWT_PUBLIC_KEY_PATH`   | `/app/keys/jwt_public.pem`                                           |
| `CORE_API_URL`          | URL interna do core na Render (`https://previopls-core.onrender.com`) |
| `LOG_LEVEL`             | `INFO`                                                                |

As chaves RSA do JWT precisam ser materializadas no container. No piloto, gere com `services/gateway/scripts/gen_rsa_keys.sh` e suba via Render Secret Files (Settings → Secret Files), mountando em `/app/keys/jwt_private.pem` e `/app/keys/jwt_public.pem`. Em produção, mova para KMS gerenciado.

## Domínio público

`api.previopls.com.br`. Settings → Custom Domains. Render gera o certificado TLS via Let's Encrypt.

## Health check

O Dockerfile do gateway já define `HEALTHCHECK` (curl em `/health`). Render usa o mesmo path por configuração.

## Limitações do plano free

- Suspende após 15 min sem tráfego. Primeiro request acorda o container.
- 750 horas-mês de runtime gratuito (suficiente se for o único serviço público).
- 100 GB de bandwidth gratuito.
- Não usar para produção continuada. Migre para Starter ($7/mês) para uptime contínuo.
