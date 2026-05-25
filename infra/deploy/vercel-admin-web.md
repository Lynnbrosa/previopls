# Vercel · admin-web

Painel Next.js do PrevioPLS. Plano Hobby (free) cobre tudo que o piloto precisa.

## Setup no painel da Vercel

1. **Import Git Repository**: aponte para `Lynnbrosa/previopls`.
2. **Root Directory**: `apps/admin-web`. Vercel detecta o Next.js automaticamente.
3. **Build Command**: deixar default (`next build`).
4. **Output Directory**: deixar default (`.next`).
5. **Install Command**: `npm install`.
6. **Node version**: 20 (Settings → General → Node.js Version).

## Variáveis de ambiente

| Var                    | Valor                                                         |
|------------------------|----------------------------------------------------------------|
| `NEXT_PUBLIC_API_URL`  | `https://api.previopls.com.br`                                |
| `INTERNAL_GATEWAY_URL` | URL interna do Gateway no Render (`https://previopls-gateway.onrender.com`) |
| `NODE_ENV`             | `production` (Vercel define sozinho)                          |

Em piloto, antes do Gateway estar exposto publicamente, aponte `INTERNAL_GATEWAY_URL` para a URL do serviço `core` na Render (`https://previopls-core.onrender.com`) para reutilizar o seed real (300 clientes, 93 leads). Decisão temporária explicada em [`apps/admin-web/README.md`](../../apps/admin-web/README.md).

## Domínio público

`app.previopls.com.br`. Configure em Settings → Domains. Vercel emite o certificado TLS automaticamente.

## Performance

O Next.js está em modo `output: 'standalone'`, mas a Vercel ignora esse output e usa a build otimizada própria (server functions + static assets na edge). Performance fica equivalente ou melhor.

## Observabilidade

- Vercel Analytics (free tier): métricas básicas de web vitals.
- Vercel Logs (live): inspeção de requests em real time pelo painel.
- Para SIEM externo no futuro, exporte logs via Vercel Log Drains (plano Pro).
