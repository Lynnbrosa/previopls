# admin-web

Painel de gestão do PrevioPLS, usado pelo gerente de pós-venda da concessionária e por stakeholders Ford em demos. Built sobre Next.js 14 App Router, Tailwind, Recharts.

## Stack

- Next.js 14.2 (App Router, server components, server actions).
- React 18.
- TypeScript 5 strict.
- Tailwind CSS 3.4 (paleta Ford `#003478`).
- Recharts para o gráfico de distribuição de perfis.
- shadcn/ui de forma manual: classes Tailwind componentizadas em `app/globals.css` (sem instalar o CLI da shadcn).

## Páginas

| Rota             | Tipo            | O que mostra                                                        |
|-------------------|------------------|---------------------------------------------------------------------|
| `/`              | redirect         | Vai para `/dashboard`.                                              |
| `/login`         | client           | Form de credenciais, POST para a API route de auth.                  |
| `/dashboard`    | server           | Cards de totais, pie chart de perfis, lista de leads críticos.       |
| `/leads`        | server           | Tabela paginada com filtros (status, prioridade, perfil).            |
| `/leads/[id]`   | server + client  | Visão 360 do lead com ações (agendar, recusado, sem contato).        |
| `/about`        | server           | Resumo da arquitetura e modelo ML, links para os docs.               |

## Autenticação

O form de login posta para `POST /api/auth/login`, uma route handler do Next.js que chama o backend (`/v1/auth/login`) usando `INTERNAL_GATEWAY_URL`. O JWT volta na resposta e é gravado num cookie httpOnly secure (`previopls_jwt`). Páginas protegidas usam o `(app)/layout.tsx`, que redireciona para `/login` quando o cookie não está presente. Logout faz POST em `/api/auth/logout`, que apenas limpa o cookie.

Todo fetch de dados acontece server-side via `lib/api.ts`, que lê o cookie e injeta `Authorization: Bearer ...` nos requests para o backend. O cliente nunca vê o JWT em JavaScript.

## Variáveis de ambiente

| Var                       | Default                  | Para que serve                                                     |
|---------------------------|---------------------------|--------------------------------------------------------------------|
| `NEXT_PUBLIC_API_URL`     | `https://localhost`       | Base pública usada por links que vão para a API externamente.       |
| `INTERNAL_GATEWAY_URL`    | `http://gateway:8000`     | Base usada pelos server components/API routes do Next.js dentro do compose. |
| `NODE_ENV`                | `production` em prod      | Padrão do Next.js.                                                  |

No `infra/docker-compose.yml`, `INTERNAL_GATEWAY_URL` está configurado para apontar ao Gateway interno. Em piloto, se o Gateway ainda não tiver users seed (Alembic do Gateway não traz seeds), aponte temporariamente para o Core (`http://core:5000`), que tem `DataSeeder` carregando admin e consultor padrão. Detalhes da decisão em `ARCHITECTURE.md`, ADR-001.

## Como rodar isolado

```bash
cd apps/admin-web
cp .env.example .env.local
# ajuste INTERNAL_GATEWAY_URL para o backend que você quer atingir
npm install
npm run dev
```

A app sobe em `http://localhost:3000`. O backend (Gateway ou Core) precisa estar respondendo na URL configurada.

## Build de produção

```bash
npm run build
npm start
```

Ou via Docker (`output: 'standalone'` no `next.config.js`):

```bash
docker build -t previopls-admin-web .
docker run -p 3000:3000 \
  -e INTERNAL_GATEWAY_URL=http://gateway:8000 \
  -e NEXT_PUBLIC_API_URL=https://app.previopls.com.br \
  previopls-admin-web
```

## Padrões de UI

- Paleta Ford `#003478` para acentos primários. Tons de cinza Tailwind para neutros.
- Tipografia Inter via `next/font/google`, fallback system stack.
- Cards com borda fina e shadow sutil. Tabelas com hover state claro.
- Sem animações decorativas, sem glassmorphism, sem CAPS gratuito.
- Headers em sentence case ou title case quando necessário, não em SHOUTING.
- Botões primários em azul Ford, secundários neutros, destrutivos em vermelho controlado.

## Adicionar nova página

1. Crie a rota em `app/.../page.tsx`.
2. Se for protegida, coloque dentro do segment `(app)/` para herdar o `AppLayout`.
3. Use server components por padrão. Marque `'use client'` apenas em componentes que precisam de estado de cliente.
4. Acesse o backend via `lib/api.ts`. Não chame `fetch` direto, para que o handling de cookie/erro fique centralizado.
