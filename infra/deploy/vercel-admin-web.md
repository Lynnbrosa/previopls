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

Como conferir: no projeto da Vercel, **Deployments** → filtro *Environment: Production*. Se o último deploy de produção for antigo enquanto os pushes recentes aparecem só como *Preview*, a Production Branch aponta para outra branch (ou o projeto foi promovido à mão uma única vez). Corrija em Settings → Git → Production Branch e faça **Redeploy** do último commit, ou use **Promote to Production** no deploy de preview mais recente. Até lá, o código novo só existe nas URLs de preview (`previopls-admin-git-<branch>-<time>.vercel.app`), que por padrão pedem login na Vercel, e a URL de produção (`previopls-admin.vercel.app`) continua servindo o build antigo: dashboard com "Falha ao carregar dados do backend. Verifique se o serviço de domínio está respondendo na rede interna." para qualquer erro.

As variáveis de ambiente valem por escopo: um preview só enxerga `INTERNAL_GATEWAY_URL` se ela também estiver marcada para *Preview*.

## Se o login mostrar erro

- "Credenciais inválidas ou conta bloqueada temporariamente": o backend respondeu 401. Confira se o Gateway na Render tem usuários (`BOOTSTRAP_ADMIN_*` ou `SEED_DEFAULT_USERS=true`, ver [`render-gateway.md`](render-gateway.md)) e se não houve 5 tentativas erradas nos últimos 15 minutos.
- "O backend demorou para responder": cold start do free tier da Render (30 a 60 s). A route de login espera até 50 s dentro do `maxDuration` de 60 s; tente de novo.
- "O servidor respondeu HTTP 504 sem detalhes": a função da Vercel foi cortada antes do backend acordar. Acorde o backend abrindo `<gateway>/health` e repita.

## Se o dashboard mostrar "Backend indisponível"

O card traz o erro da leitura (status e código do backend) e um diagnóstico da cadeia, medido pelo próprio servidor do painel no momento da falha:

| Linha | O que mede | Se estiver "fora" ou "sem resposta" |
|---|---|---|
| Painel → Gateway | `GET <INTERNAL_GATEWAY_URL>/health` | URL errada ou variável não definida (o card avisa quando está usando o default `gateway:8000` do compose); Gateway suspenso no free tier (acorda em 30 a 60 s) |
| Gateway → Banco | `components.database` do `/health` | `DATABASE_URL` do Gateway na Render / Neon fora |
| Gateway → Core | `components.core` do `/health` | Core ainda acordando (1 a 2 min em JVM) ou `CORE_API_URL` errada |

Códigos que aparecem na mensagem:

- `503 CORE_UNAVAILABLE`: o Gateway não conseguiu falar com o Core. Transitório em free tier; o card tenta de novo a cada 20 s (até 15 vezes) e some sozinho quando o Core sobe.
- `502 CORE_AUTH_MISMATCH`: o Core rejeitou o token interno do Gateway. `JWT_SECRET` precisa ser idêntico nos dois serviços da Render. Não é transitório: o card não insiste.
- `HTTP 504` sem código: a função da Vercel foi cortada. As páginas declaram `maxDuration = 60`, o máximo do plano Hobby sem Fluid Compute; não aumente sem mudar de plano.

## Domínio público

`app.previopls.com.br`. Configure em Settings → Domains. Vercel emite o certificado TLS automaticamente.

## Performance

O Next.js está em modo `output: 'standalone'`, mas a Vercel ignora esse output e usa a build otimizada própria (server functions + static assets na edge). Performance fica equivalente ou melhor.

## Observabilidade

- Vercel Analytics (free tier): métricas básicas de web vitals.
- Vercel Logs (live): inspeção de requests em real time pelo painel.
- Para SIEM externo no futuro, exporte logs via Vercel Log Drains (plano Pro).
