# Neon · Postgres

Banco gerenciado serverless, plano free. Duas bases isoladas para Core e Gateway, espelhando a divisão do compose local.

## Setup

1. Criar conta em <https://neon.tech>.
2. Criar projeto `previopls`. Região: `aws-sa-east-1` (São Paulo) se disponível, senão `aws-us-east-1`.
3. Renomear o database default para `previopls_core`.
4. Pelo SQL Editor do Neon, executar:

   ```sql
   CREATE DATABASE previopls_gateway;
   ```

5. Para cada base, criar role de aplicação:

   ```sql
   -- como neon_superuser na base previopls_core
   CREATE ROLE previopls_core_app LOGIN PASSWORD '<random-32-bytes>';
   GRANT ALL ON SCHEMA public TO previopls_core_app;
   GRANT ALL ON ALL TABLES IN SCHEMA public TO previopls_core_app;
   ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO previopls_core_app;
   ```

   Repetir para `previopls_gateway_app` na base `previopls_gateway`.

6. Anotar as connection strings de cada base (formato `postgresql://user:pass@host/db?sslmode=require`).

## Branching

Neon permite criar branches do banco a custo zero (copy-on-write). Recomendado:

- Branch `main` (produção).
- Branch `staging` (homologação).
- Branch `pr-*` (criados sob demanda em PRs grandes).

Cada branch tem connection string própria. O Render aponta para `main` em produção; staging pode subir um Render service paralelo.

## Variáveis de ambiente derivadas

| Serviço     | Connection string                                                              |
|-------------|---------------------------------------------------------------------------------|
| `core`      | `jdbc:postgresql://<host>/previopls_core?sslmode=require` (formato JDBC)        |
| `gateway`   | `postgresql+psycopg://<user>:<pass>@<host>/previopls_gateway?sslmode=require`  |

Note a diferença de prefixo: JDBC para Java, dialeto SQLAlchemy para Python.

## Limites do plano free

- 3 GB armazenamento agregado entre todas as bases e branches.
- Compute scale to zero após 5 min de inatividade (cold start de 1 a 2 s).
- Logs retidos por 7 dias.
- Sem replicas leitura (paid).

Suficiente para piloto. Para produção, plano Launch ($19/mês) entrega 10 GB e compute sempre quente.

## Backup

Plano free inclui Point-In-Time Recovery dos últimos 7 dias automaticamente, sem configuração adicional. Para backup ofline:

```bash
pg_dump "postgresql://user:pass@host/previopls_core?sslmode=require" > backup_core.sql
```
