Nomes e RMs,
Giovanne Charelli Zaniboni Silva | 556223 
Leonardo Pasquini Baldaia | 557416 
Gustavo Oliveira de Moura | 555827 
Lynn Bueno Rosa | 551102

# PrevioPLS — Ford Predict & Care (Backend)

Plataforma preditiva de retenção pós-venda Ford. Backend SOA em **Java 21 + Spring Boot 3 + Spring Data JPA + PostgreSQL + Flyway**.

Entrega da Sprint Ford FIAP 2026 — Arquitetura Orientada a Serviços e Web Services.

## Visão geral

No momento da compra (D0), o backend recebe os dados comerciais do veículo + cliente, classifica o comprador em um dos 4 perfis (Fiel / Abandono / Esquecido / Econômico) via motor ML, e — quando o perfil é de risco — gera um **lead priorizado** consumido pelo app mobile do consultor de serviços.

Regra crítica de produto (US02): a predição usa **apenas variáveis disponíveis no momento da compra**. Nenhum dado pós-compra entra no input do motor.

## Stack

- Java 21
- Spring Boot 3.3 (Web, Data JPA, Security, Validation)
- Hibernate 6
- PostgreSQL 14+ (H2 em memória nos testes)
- Flyway (migrações)
- jjwt 0.12 (assinatura HS256)
- springdoc-openapi 2.6 (Swagger UI auto-gerado em `/docs`)
- Maven

## Arquitetura

Camadas: **controller → service → repository (JpaRepository) → entity** (SOA estrita, ver [docs/architecture.md](docs/architecture.md)).

```
HTTP → controller → service → repository (Spring Data) → entity (Hibernate)
                       ↓
                  MlService (motor preditivo)
```

## Estrutura de pastas

```
PrevioPLS/
├── pom.xml
├── README.md
├── swagger.json                       # contrato OpenAPI 3 (snapshot)
├── docs/architecture.md               # diagramas mermaid
├── .env.example
├── .gitignore
└── src/
    ├── main/
    │   ├── java/com/previopls/
    │   │   ├── PrevioPlsApplication.java       # @SpringBootApplication
    │   │   ├── config/
    │   │   │   ├── SecurityConfig.java         # SecurityFilterChain + BCrypt + CORS
    │   │   │   ├── JwtAuthFilter.java          # lê Bearer header, popula SecurityContext
    │   │   │   ├── WebConfig.java              # converters de enum (query params)
    │   │   │   ├── OpenApiConfig.java          # bearerAuth security scheme
    │   │   │   └── DataSeeder.java             # CommandLineRunner — cria admin/consultor
    │   │   ├── controller/
    │   │   │   ├── AuthController.java         # POST /v1/auth/login
    │   │   │   ├── ClienteController.java      # POST /v1/clientes (ADMIN)
    │   │   │   ├── LeadController.java         # GET/PATCH /v1/leads[/{id}] (CONSULTOR/ADMIN)
    │   │   │   └── MetaController.java         # GET /health · /version
    │   │   ├── service/
    │   │   │   ├── AuthService.java
    │   │   │   ├── ClienteService.java         # orquestra D0 → classificação → lead
    │   │   │   ├── LeadService.java
    │   │   │   ├── MlService.java              # motor preditivo (stub)
    │   │   │   └── JwtService.java             # gera/valida JWT HS256
    │   │   ├── repository/                     # Spring Data JpaRepository
    │   │   │   ├── UsuarioRepository.java
    │   │   │   ├── ClienteRepository.java
    │   │   │   ├── VeiculoRepository.java
    │   │   │   └── LeadRepository.java         # findFiltered com CASE WHEN
    │   │   ├── entity/
    │   │   │   ├── Usuario.java
    │   │   │   ├── Cliente.java
    │   │   │   ├── Veiculo.java
    │   │   │   ├── Lead.java
    │   │   │   └── enums/                      # RolePapel, PerfilCliente, PrioridadeLead, StatusLead
    │   │   ├── dto/                            # records (Java 17+)
    │   │   │   ├── auth/, cliente/, lead/, meta/
    │   │   │   └── ErrorResponse.java
    │   │   ├── mapper/                         # entity ↔ DTO
    │   │   └── exception/
    │   │       ├── AppException.java           # base
    │   │       ├── NotFoundException.java
    │   │       ├── ConflictException.java
    │   │       ├── UnauthorizedException.java
    │   │       ├── ForbiddenException.java
    │   │       └── GlobalExceptionHandler.java # @RestControllerAdvice
    │   └── resources/
    │       ├── application.yml
    │       ├── application-test.yml
    │       └── db/migration/V1__initial_schema.sql
    └── test/
        └── java/com/previopls/service/ClienteServiceTest.java   # Mockito
```

## Endpoints (contrato — ver [swagger.json](swagger.json))

| Método | Rota                                          | Papel mínimo       | Descrição                                                                 |
|--------|-----------------------------------------------|--------------------|--------------------------------------------------------------------------|
| GET    | `/health`                                     | público            | Liveness/readiness — sonda o banco                                       |
| GET    | `/version`                                    | público            | Nome, versão e build do serviço                                          |
| POST   | `/v1/auth/login`                              | público            | Autentica e retorna JWT (campo `role`: `admin` / `consultor`)            |
| POST   | `/v1/clientes`                                | ADMIN              | Input D0 da compra → cria cliente+veículo, dispara classificação, gera lead |
| GET    | `/v1/leads?prioridade=alta&status=aberto`     | CONSULTOR ou ADMIN | Lista paginada de leads (filtros + ordenação por prioridade e score)     |
| GET    | `/v1/leads/{id}`                              | CONSULTOR ou ADMIN | Visão 360 — cliente + veículo + script comercial                         |
| PATCH  | `/v1/leads/{id}`                              | CONSULTOR ou ADMIN | Atualiza status (`agendado` / `recusado` / `sem-contato`)                |

Endpoints de negócio são versionados sob `/v1/` para permitir evolução do contrato sem quebrar o app mobile já distribuído. `/health` e `/version` permanecem fora do versionamento (padrão de infraestrutura).

Swagger UI interativo: `http://localhost:5000/docs`. OpenAPI JSON ao vivo: `http://localhost:5000/v3/api-docs`.

## Setup local

### 1. Pré-requisitos

- JDK 21
- Maven 3.9+ (ou `./mvnw` se você adicionar o wrapper)
- PostgreSQL 14+ rodando localmente

### 2. Banco

```bash
psql -U postgres -c "CREATE DATABASE previopls;"
```

### 3. Variáveis de ambiente

Copie `.env.example` para `.env` (ou exporte direto no shell):

```bash
export DATABASE_URL=jdbc:postgresql://localhost:5432/previopls
export DB_USERNAME=postgres
export DB_PASSWORD=postgres
export JWT_SECRET=trocar-em-producao-usar-chave-com-pelo-menos-32-bytes-aleatoria
```

### 4. Compilar e rodar

```bash
mvn clean package
mvn spring-boot:run
```

Aplicação em `http://localhost:5000`.

- Swagger UI: `http://localhost:5000/docs`
- OpenAPI JSON: `http://localhost:5000/v3/api-docs`

Na primeira inicialização:
- **Flyway** aplica `V1__initial_schema.sql` (schema) e `V2__seed_real_data.sql` (300 clientes + 93 leads derivados da planilha Ford real — ver seção [Migrações](#migrações-flyway))
- **DataSeeder** cria os usuários padrão:

| Email                  | Senha    | Papel     |
|------------------------|----------|-----------|
| `admin@ford.com`       | `admin123` | ADMIN     |
| `consultor@ford.com`   | `cons123`  | CONSULTOR |

## Variáveis de ambiente

| Var                     | Default                                              | Descrição                              |
|-------------------------|------------------------------------------------------|----------------------------------------|
| `DATABASE_URL`          | `jdbc:postgresql://localhost:5432/previopls`         | URL JDBC                               |
| `DB_USERNAME`           | `postgres`                                           | Usuário do banco                       |
| `DB_PASSWORD`           | `postgres`                                           | Senha do banco                         |
| `JWT_SECRET`            | (dev only — trocar em prod, mínimo 32 bytes)         | Chave HMAC HS256                       |
| `JWT_EXPIRATION_HOURS`  | `8`                                                  | Expiração do access token              |
| `CORS_ORIGINS`          | `http://localhost:8081,http://localhost:19006`       | Origens autorizadas (vírgula)          |

## Fluxo de uso (end-to-end)

### 1) Login

```bash
curl -X POST http://localhost:5000/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"consultor@ford.com","senha":"cons123"}'
```

Resposta:
```json
{
  "accessToken": "eyJhbGc...",
  "tokenType": "Bearer",
  "expiresIn": 28800,
  "role": "consultor"
}
```

### 2) Cadastrar cliente D0 (admin)

```bash
curl -X POST http://localhost:5000/v1/clientes \
  -H "Authorization: Bearer <TOKEN_ADMIN>" \
  -H "Content-Type: application/json" \
  -d '{
    "nome":"Maria Silva",
    "cpf":"12345678900",
    "email":"maria@example.com",
    "telefone":"+5511999998888",
    "regiao":"SP",
    "veiculo":{
      "modelo":"Ranger",
      "versao":"XLT",
      "ano":2026,
      "vin":"9BFZZZ8F7NB000001",
      "dataCompra":"2026-05-13",
      "valorCompra":"250000.00",
      "concessionariaId":"FORD-SP-001"
    }
  }'
```

`ClienteService.cadastrarCompra` é `@Transactional`: persiste cliente+veículo, chama `MlService.classificar`, grava `perfil` + `scoreRisco` + `classificadoEm` no cliente e — se o perfil for `ABANDONO` ou `ESQUECIDO` — cria um lead com prioridade derivada do score (`≥0.85 → CRITICA`, `≥0.65 → ALTA`, `≥0.40 → MEDIA`, senão `BAIXA`).

### 3) Listar leads no app mobile (consultor)

```bash
curl "http://localhost:5000/v1/leads?prioridade=alta&status=aberto&page=1&per_page=20" \
  -H "Authorization: Bearer <TOKEN_CONSULTOR>"
```

A query ordena por `prioridade` (CRITICA → ALTA → MEDIA → BAIXA via CASE WHEN no JPQL), depois `scoreRisco DESC`, depois `criadoEm DESC`.

### 4) Visão 360

```bash
curl http://localhost:5000/v1/leads/<id> \
  -H "Authorization: Bearer <TOKEN_CONSULTOR>"
```

### 5) Registrar resultado

```bash
curl -X PATCH http://localhost:5000/v1/leads/<id> \
  -H "Authorization: Bearer <TOKEN_CONSULTOR>" \
  -H "Content-Type: application/json" \
  -d '{"status":"agendado","observacao":"agendado p/ 18/05 às 14h"}'
```

## Tratamento de erros

`GlobalExceptionHandler` (`@RestControllerAdvice`) intercepta tudo e retorna JSON estruturado. **Nunca** vaza stack trace para o cliente — `server.error.include-stacktrace=never` no `application.yml` + handler explícito por tipo de exceção. Erros não previstos geram um `incident_id` no log para correlação:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Dados inválidos",
    "details": { "cpf": "CPF deve conter 11 dígitos numéricos" }
  }
}
```

Códigos: `VALIDATION_ERROR` (422), `BAD_REQUEST` (400), `UNAUTHORIZED` (401), `FORBIDDEN` (403), `NOT_FOUND` (404), `CONFLICT` (409), `METHOD_NOT_ALLOWED` (405), `INTERNAL_ERROR` (500).

## Segurança — controles implementados

Mapeamento contra a rubrica de **Cybersecurity** (100 pts) da challenge:

### 1. Validação de entrada (20 pts)

- **Jakarta Validation** em todos os DTOs: `@NotBlank`, `@Pattern` (CPF 11 dígitos, VIN 17 chars sem I/O/Q), `@Email`, `@Size`, `@Min/@Max`, `@DecimalMin`.
- **Anti-SQLi por design**: Spring Data JPA parametriza tudo — não há string interpolation em queries.
- **Anti-XSS**: campo livre `observacao` no PATCH de lead passa por `Encode.forHtmlContent` (OWASP Java Encoder) + remoção de caracteres de controle ([`LeadService.sanitize`](src/main/java/com/previopls/service/LeadService.java)).
- **Body/header limits** no Tomcat ([`PayloadSizeConfig`](src/main/java/com/previopls/config/PayloadSizeConfig.java)): max-post-size 1MB, max-http-header-size 16KB, maxParameterCount 100 — defesa contra payload flooding.
- **Sem stack trace**: `server.error.include-stacktrace=never` + `GlobalExceptionHandler` que devolve `{error:{code,message,details}}` uniforme. Erros internos geram `incident_id` correlacionável nos logs.

### 2. Autenticação e autorização (20 pts)

- **JWT HS256** assinado com chave validada no boot (≥32 bytes). Expiração curta (8h default).
- **BCrypt cost 12** para senhas (acima do default 10).
- **RBAC** via `@PreAuthorize("hasRole('ADMIN')")` e `hasAnyRole('CONSULTOR','ADMIN')` nos controllers.
- **Anti-brute-force**: tabela `login_attempts` registra cada tentativa. Após 5 falhas em 15 min, o email é bloqueado por 15 min ([`LockoutService`](src/main/java/com/previopls/service/LockoutService.java)). Configurável via `LOCKOUT_MAX_ATTEMPTS` / `LOCKOUT_WINDOW_MINUTES`.
- **Auditoria de cada login** (sucesso, falha, bloqueio) via `AuditService`.

### 3. Proteção de APIs (20 pts)

- **HTTPS/TLS 1.2+**: terminação esperada em nginx/ALB em produção. HSTS forçado via header (1 ano + subdomínios + preload) — ver `SecurityHeadersFilter`.
- **Rate limiting** in-memory por IP via **Bucket4j** ([`RateLimitFilter`](src/main/java/com/previopls/config/RateLimitFilter.java)): 5/min em `/v1/auth/login`, 200/min nos demais endpoints autenticados. Endpoints de saúde (`/health`, `/version`) são isentos.
- **CORS** com whitelist explícita (`CORS_ORIGINS`); `setAllowedOriginPatterns` + `allowCredentials=true`; headers permitidos restritos a `Authorization`, `Content-Type`, `X-Request-Id`.
- **Security headers** aplicados a toda resposta ([`SecurityHeadersFilter`](src/main/java/com/previopls/config/SecurityHeadersFilter.java)):
  - `Strict-Transport-Security: max-age=31536000; includeSubDomains; preload`
  - `X-Frame-Options: DENY` (anti-clickjacking)
  - `X-Content-Type-Options: nosniff`
  - `Referrer-Policy: no-referrer`
  - `Permissions-Policy` desabilitando geolocation/microphone/camera/payment/usb
  - `Content-Security-Policy: default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'`

### 4. Segurança de dados e privacidade (25 pts)

- **Criptografia em repouso** com **AES-256-GCM** ([`CryptoService`](src/main/java/com/previopls/crypto/CryptoService.java)) aplicada via `JPA AttributeConverter` em `clientes.email` e `clientes.telefone` — transparente pro código de negócio. IV aleatório por chamada, mesma plaintext → ciphertexts diferentes. Tag de autenticação 128 bits.
- **Chave AES** carregada de `APP_CRYPTO_KEY` (Base64 de 32 bytes). Validada no boot — falha se tamanho errado. Em prod: variável aponta para KMS/Vault, **nunca** o `application.yml`.
- **CPF não é criptografado** (busca por igualdade exigiria coluna auxiliar de hash, custo desproporcional); é sempre mascarado nas respostas via `Pii.maskCpf` ([`Pii.java`](src/main/java/com/previopls/crypto/Pii.java)) — só os 3 primeiros e 2 últimos dígitos aparecem.
- **Email/telefone também são mascarados** nas respostas mesmo após decriptação no Hibernate — defesa em profundidade.
- **Política de retenção**: coluna `clientes.retencao_ate` reservada para job futuro que anonimiza PII após o prazo (LGPD).
- **Anonimização**: o mascaramento de PII via `Pii.*` produz versões prontas para uso em dashboards e datasets de ML sem expor o original.
- **Logs sem PII**: o `PiiMaskingConverter` do Logback intercepta TODAS as mensagens antes da escrita, mascarando CPF, email, header `Authorization: Bearer ...` e sequências longas de dígitos. Defesa contra `Logger.info("user={}", obj)` que vazaria PII por acidente.

### 5. Monitoramento, logs e auditoria (15 pts)

- **Logs estruturados**: pattern de console em dev; encoder JSON (logstash-logback) no profile `prod`. Cada linha carrega o `requestId` no MDC.
- **Request ID** automático ([`RequestIdFilter`](src/main/java/com/previopls/config/RequestIdFilter.java)): aceita `X-Request-Id` do cliente, gera UUID se ausente, propaga no MDC e ecoa no header de resposta — permite rastrear uma requisição ponta a ponta.
- **Trilha de auditoria** (tabela `audit_logs`) registra:
  - `LOGIN_SUCCESS`, `LOGIN_FAILED`, `LOGIN_LOCKED` (com email, IP, user-agent)
  - `CLIENTE_CREATED` (com perfil + score)
  - `LEAD_CREATED`, `LEAD_PATCHED` (com transição de status)
  - `UNAUTHORIZED_ACCESS` (401), `FORBIDDEN_ACCESS` (403) — detecta tentativas de quebra de RBAC
- **Eventos suspeitos**: o lockout cobre tentativas repetidas. Para detecção mais ampla, querys SQL sobre `audit_logs` agrupando por IP + janela de tempo (consultas massivas, tentativas de escalation) — exemplo no README abaixo.

### Operações de segurança comuns

```sql
-- Tentativas de login falhas nas últimas 24h, agrupadas por email
SELECT actor_email, count(*) FROM audit_logs
WHERE action = 'LOGIN_FAILED' AND occurred_at > NOW() - INTERVAL '24 hours'
GROUP BY actor_email ORDER BY count DESC LIMIT 20;

-- IPs com mais 401/403 (possível scanner)
SELECT remote_ip, action, count(*) FROM audit_logs
WHERE action IN ('UNAUTHORIZED_ACCESS','FORBIDDEN_ACCESS')
  AND occurred_at > NOW() - INTERVAL '1 hour'
GROUP BY remote_ip, action ORDER BY count DESC LIMIT 20;

-- Histórico de mudanças de status de um lead
SELECT occurred_at, actor_email, details FROM audit_logs
WHERE action = 'LEAD_PATCHED' AND entity_id = '<uuid-do-lead>'
ORDER BY occurred_at DESC;
```

### Resumo do hardening por arquivo

| Arquivo                                                     | Controle                                       |
|-------------------------------------------------------------|------------------------------------------------|
| `crypto/CryptoService.java`                                  | AES-256-GCM (cifrar/decifrar PII)             |
| `crypto/EncryptedStringConverter.java`                       | JPA AttributeConverter transparente            |
| `crypto/Pii.java`                                            | Máscaras determinísticas (CPF/email/telefone) |
| `config/RateLimitFilter.java`                                | Bucket4j por IP, 5/min login + 200/min default |
| `config/SecurityHeadersFilter.java`                          | HSTS, CSP, X-Frame, etc                       |
| `config/RequestIdFilter.java`                                | Correlation ID no MDC + header                |
| `config/PayloadSizeConfig.java`                              | Body 1MB, header 16KB                         |
| `config/SecurityConfig.java`                                 | JWT filter, CORS, audit em 401/403            |
| `service/AuditService.java`                                  | Persiste eventos em `audit_logs`              |
| `service/LockoutService.java`                                | Anti-brute-force no login                     |
| `security/PiiMaskingConverter.java`                          | Logback masking de PII                        |
| `resources/logback-spring.xml`                               | JSON estruturado + masking                    |
| `migration/V3__security_hardening.sql`                       | Schemas de audit + alter clientes              |

## Testes

```bash
mvn test
```

`ClienteServiceTest` (Mockito) prova o desacoplamento entre service e camada de persistência:

- gera lead crítico quando perfil é `ABANDONO` e score ≥ 0.85
- não gera lead para perfil `FIEL`
- rejeita CPF duplicado (409 Conflict)
- rejeita VIN duplicado (409 Conflict)

Os repositórios são mockados; o service roda sem banco real.

## Migrações (Flyway)

| Migration                          | Conteúdo                                                                                                        |
|------------------------------------|-----------------------------------------------------------------------------------------------------------------|
| `V1__initial_schema.sql`           | 4 tabelas (usuarios/clientes/veiculos/leads), índices compostos `(prioridade, status)`, CHECK nos enums          |
| `V2__security_hardening.sql`       | Tabelas `audit_logs` + `login_attempts`; muda `clientes.email/telefone` para TEXT (ciphertext AES-GCM); coluna `retencao_ate` |
| `V3__seed_real_data.sql`           | 300 clientes + 300 veículos + 93 leads gerados a partir da planilha Ford pelo time IA/ML. Email/telefone JÁ criptografados em AES-256-GCM (formato compatível com o `EncryptedStringConverter` do backend). |

Flyway aplica automaticamente no boot. Para criar uma nova migração, basta adicionar `V3__descricao.sql` em `src/main/resources/db/migration/`.

### Seed de dados reais

O seed (`V3`) usa **dados D0 reais** da planilha oficial Ford (`Downloads/Ford/vin_share_Desafio_02.xlsx`) — respeita a US02 (apenas variáveis disponíveis no momento da compra entram na classificação):

| Campo no PrevioPLS              | Origem na planilha Ford                                                  |
|---------------------------------|--------------------------------------------------------------------------|
| `veiculos.modelo`               | `ModelName` (Ranger, Transit, Maverick, F-150, Bronco Sport, etc.)       |
| `veiculos.ano`                  | `ModelYear` (2018–2026)                                                  |
| `veiculos.data_compra`          | `SalesDate`                                                              |
| `veiculos.concessionaria_id`    | `DealerCode` (prefixado com `FORD-`)                                     |
| `veiculos.vin`                  | Primeiros 17 chars do `VIN_Hash` (uppercase, mantém padrão alfanumérico) |
| `clientes.perfil`, `score_risco`| Computados pelo mesmo SHA-256 do `MlService.classificar` (Java)          |
| `clientes.nome/cpf/email/telefone/regiao` | Sintéticos, determinísticos por `VIN_Hash` (a planilha está anonimizada) |

Distribuição resultante: ~39% Fiel, ~30% Econômico, ~17% Esquecido, ~14% Abandono → **93 leads** gerados automaticamente (Abandono + Esquecido) com prioridades distribuídas entre Crítica/Alta/Média.

### Regenerar o seed

O script gerador (`build_seed.py`) vive no repositório **IA/ML** (`challenge-IAML`) porque é um pipeline de preparação de dados — Python, sklearn, criptografia AES.

Para gerar uma nova versão do `V3__seed_real_data.sql`:

1. Clone também o repo IA/ML: `git clone https://github.com/Lynnbrosa/challenge-IAML.git`
2. Siga o README de lá pra obter a planilha Ford e rodar `python scripts/build_seed.py`.
3. Aponte o output diretamente para esta pasta de migrations:

```bash
APP_CRYPTO_KEY=<mesma-do-backend> \
  python scripts/build_seed.py \
    data/vin_share_Desafio_02.xlsx \
    300 \
    ../challenge-SOA/src/main/resources/db/migration/V3__seed_real_data.sql
```

A `APP_CRYPTO_KEY` usada na geração precisa ser **a mesma** que o backend Java vai consumir — senão a decriptação Fernet falha ao ler os clientes.

## Rubrica × entregas

| Rubrica (item)                                  | Onde está                                                                 |
|-------------------------------------------------|--------------------------------------------------------------------------|
| Diagrama de arquitetura (10%)                   | [docs/architecture.md](docs/architecture.md) — flowchart + 2 sequence + ER |
| APIs RESTful + Swagger (20%)                    | [swagger.json](swagger.json) + Swagger UI em `/docs`                     |
| Uso correto de métodos HTTP (10%)               | POST (cria) / GET (lê) / PATCH (parcial) + 201/200/404/409/422            |
| README + Swagger contrato (10%)                 | este README + `swagger.json`                                              |
| SOA — camadas (20%)                             | `controller → service → repository → entity`; teste Mockito comprova desacoplamento |
| REST + JSON + erros sem stack (15%)             | `GlobalExceptionHandler` + `server.error.include-stacktrace=never`        |
| JPA + migrações (15%)                           | `entity/*` (Hibernate) + `migration/V1__initial_schema.sql` (Flyway)      |

## Repositórios irmãos da challenge

- [`challenge-Mobile`](https://github.com/Lynnbrosa/challenge-Mobile) — app React Native do consultor (consome esta API)
- [`challenge-IAML`](https://github.com/Lynnbrosa/challenge-IAML) — notebook IA/ML + gerador do seed (`V3__seed_real_data.sql` deste repo)
- [`challenge-Cyber`](https://github.com/Lynnbrosa/challenge-Cyber) — controles paralelos de Cybersecurity / LGPD em Python (Fernet, audit, HMAC, TLS)
