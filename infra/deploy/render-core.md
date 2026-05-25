# Render · core

Serviço Spring Boot 3 que persiste o domínio e dispara a classificação ML.

## Setup no painel da Render

1. **New** → **Web Service**.
2. **Connect a repository**: `Lynnbrosa/previopls`.
3. **Name**: `previopls-core`.
4. **Root Directory**: `services/core`.
5. **Runtime**: `Docker`. Dockerfile do próprio diretório (`services/core/Dockerfile`, autodetectado pelo Render).
6. **Plan**: Free.
7. **Health Check Path**: `/health`.

## Variáveis de ambiente

| Var                       | Valor                                                                 |
|---------------------------|------------------------------------------------------------------------|
| `DATABASE_URL`            | `jdbc:postgresql://<neon-host>/previopls_core?sslmode=require`        |
| `DB_USERNAME`             | usuário Neon                                                          |
| `DB_PASSWORD`             | senha Neon                                                            |
| `JWT_SECRET`              | mesmo segredo HS256 (32 bytes mínimo)                                 |
| `JWT_EXPIRATION_HOURS`    | `8`                                                                   |
| `APP_CRYPTO_KEY`          | base64 de 32 bytes (AES-256-GCM de PII)                               |
| `ML_API_URL`              | URL interna do ml-api (`https://previopls-ml-api.onrender.com`)       |
| `CORS_ORIGINS`            | `https://app.previopls.com.br,https://api.previopls.com.br`           |
| `LOCKOUT_MAX_ATTEMPTS`    | `5`                                                                   |
| `LOCKOUT_WINDOW_MINUTES`  | `15`                                                                  |
| `RATE_LIMIT_LOGIN`        | `5`                                                                   |
| `RATE_LIMIT_DEFAULT`      | `200`                                                                 |

## Domínio público

Nenhum domínio customizado. O Core fica acessível apenas pela URL interna `*.onrender.com`, usada pelo Gateway e pelo admin-web (em piloto). Em produção, configurar regras de firewall para que apenas o Gateway possa chamar o Core.

## Migrations

Flyway aplica automaticamente no boot. Inclui V3 com seed de 300 clientes + 93 leads. Para piloto Ford limpo, restringir a V2 via `SPRING_FLYWAY_TARGET=2` antes do primeiro deploy.

## Limitações conhecidas

- Cold start em JVM com Spring Boot é mais lento que FastAPI (1 a 2 min do zero). Acordar antes da demo.
- Plano free tem 512 MB de RAM. Para JVM, isso é justo. Ajuste `MaxRAMPercentage=75` no Dockerfile (já configurado).
