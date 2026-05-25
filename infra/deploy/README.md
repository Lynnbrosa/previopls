# Deploy

Stack de deploy escolhida para o piloto do PrevioPLS, priorizando free tier sem cartão de crédito amarrado. A operação é manual: estes arquivos servem como manual de provisionamento para a equipe.

## Topologia

```
Internet
  │
  ├─ app.previopls.com.br        ──► Vercel · admin-web (Next.js)
  ├─ api.previopls.com.br        ──► Render · gateway (FastAPI público)
  │
  └─ rede privada Render
        ├─ core (Spring Boot, sem URL pública)
        ├─ ml-api (FastAPI sklearn, sem URL pública)
        └─ Neon Postgres (serverless, branched dev/prod)
```

Três provedores, todos free tier:

| Camada      | Provedor   | Plano             | O que ganha free                                                                  |
|-------------|------------|--------------------|------------------------------------------------------------------------------------|
| Front       | Vercel     | Hobby              | Builds ilimitados, domínio gratuito, edge caching, SSL automático                  |
| Backends    | Render     | Free Web Services  | Build a partir de Docker, TLS automático, suspende após 15 min sem tráfego        |
| Banco       | Neon       | Free               | 3 GB armazenamento, branching por ambiente, autoscale to zero                     |

A suspensão da Render no plano free é aceitável para o piloto (primeira request acorda em 30 a 60 s). Para produção contínua, migra para o plano Starter, que mantém o serviço ativo.

## Por que não Railway

Railway não oferece tier 100% gratuito permanente sem cartão. Cobra a partir de um pequeno crédito mensal. Para esta avaliação (Ford lê o repositório e pode subir uma demo sem se comprometer com cobrança), Vercel + Render + Neon entrega o mesmo resultado com zero custo.

## Sequência de provisionamento

1. Criar o projeto no Neon. Criar duas bases: `previopls_core` e `previopls_gateway`. Anotar a connection string de cada uma.
2. Subir o ml-api no Render (web service via Dockerfile). Não expor publicamente.
3. Subir o core no Render. Apontar `DATABASE_URL` para a base `previopls_core` no Neon. Apontar `ML_API_URL` para a URL interna do ml-api.
4. Subir o gateway no Render. Apontar `DATABASE_URL` para `previopls_gateway`. Expor publicamente como `api.previopls.com.br`.
5. Importar o admin-web no Vercel. Setar `INTERNAL_GATEWAY_URL` e `NEXT_PUBLIC_API_URL`. Mapear o domínio `app.previopls.com.br`.

## Variáveis compartilhadas entre serviços

Vivem em escopo de projeto e cada serviço referencia, evitando duplicação:

- `JWT_SECRET` (32 bytes mínimo).
- `APP_CRYPTO_KEY` (base64 de 32 bytes, AES do Core).
- `FERNET_KEY` (chave Fernet do Gateway).
- `HMAC_PAYLOAD_SECRET` (assinatura do webhook de faturamento).
- `CPF_HASH_PEPPER` (pepper do hash de CPF no Gateway).

Gere com:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

## Specs por serviço

- [`vercel-admin-web.md`](vercel-admin-web.md): build Next.js standalone, env vars, mapeamento de domínio.
- [`render-gateway.md`](render-gateway.md): web service Dockerfile, TLS público, segredos.
- [`render-core.md`](render-core.md): web service Dockerfile, conexão privada com ml-api.
- [`render-ml-api.md`](render-ml-api.md): web service Dockerfile, rede interna, modelo embutido no container.
- [`neon-postgres.md`](neon-postgres.md): criação das duas bases, branching dev/prod, backup automático.

Não execute deploy automático. Confirme com o dono do projeto antes de qualquer push para o ambiente de produção.
