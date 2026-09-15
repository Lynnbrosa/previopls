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

O painel autentica no Gateway (JWT RS256) e o Gateway repassa as leituras/escritas de leads ao Core com o JWT interno HS256, então o seed real (300 clientes, 93 leads) aparece no painel sem apontar para o Core. Se precisar de um setup isolado sem Gateway, `INTERNAL_GATEWAY_URL` também aceita a URL do Core: o painel entende os dois contratos de login (ver [`apps/admin-web/README.md`](../../apps/admin-web/README.md)).

As variáveis precisam estar no escopo **Production** (e Preview, se quiser testar PRs). Uma `INTERNAL_GATEWAY_URL` definida só em Preview deixa a produção com o default `http://gateway:8000`, inalcançável na Vercel: o painel mostra "Não foi possível conectar ao backend gateway:8000".

## Branch de produção

Em Settings → Git, confirme que a Production Branch é a branch padrão do repositório (`feat/monorepo-consolidation`). Um deploy de produção preso a uma branch antiga mantém o painel com o código anterior, em que qualquer erro de login aparecia como "Credenciais inválidas".

## Se o login mostrar erro

- "Credenciais inválidas ou conta bloqueada temporariamente": o backend respondeu 401. Confira se o Gateway na Render tem usuários (`BOOTSTRAP_ADMIN_*` ou `SEED_DEFAULT_USERS=true`, ver [`render-gateway.md`](render-gateway.md)) e se não houve 5 tentativas erradas nos últimos 15 minutos.
- "O backend demorou para responder": cold start do free tier da Render (30 a 60 s). A route de login espera até 60 s (`maxDuration`); tente de novo.
- "O servidor respondeu HTTP 504 sem detalhes": a função da Vercel foi cortada antes do backend acordar. Acorde o backend abrindo `<gateway>/health` e repita.

## Domínio público

`app.previopls.com.br`. Configure em Settings → Domains. Vercel emite o certificado TLS automaticamente.

## Performance

O Next.js está em modo `output: 'standalone'`, mas a Vercel ignora esse output e usa a build otimizada própria (server functions + static assets na edge). Performance fica equivalente ou melhor.

## Observabilidade

- Vercel Analytics (free tier): métricas básicas de web vitals.
- Vercel Logs (live): inspeção de requests em real time pelo painel.
- Para SIEM externo no futuro, exporte logs via Vercel Log Drains (plano Pro).
