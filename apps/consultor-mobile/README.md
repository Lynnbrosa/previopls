Nomes e RMs,
Giovanne Charelli Zaniboni Silva | 556223 
Leonardo Pasquini Baldaia | 557416 
Gustavo Oliveira de Moura | 555827 
Lynn Bueno Rosa | 551102
# PrevioPLS Mobile

App do **Consultor de Serviços** Ford — Sprint Mobile da challenge FIAP 2026.

Atende às histórias **US05** (lista de leads do dia), **US06** (visão 360) e **US07** (registro de status). Consome o backend Spring Boot — repositório [`challenge-SOA`](https://github.com/Lynnbrosa/challenge-SOA).

## Stack

- **React Native** 0.74 + **Expo SDK 51**
- **Expo Router** (file-based, typed routes)
- **TypeScript** strict
- **Zustand** (estado)
- **Axios** com interceptor JWT
- **expo-secure-store** (JWT) + **AsyncStorage** (cache de leads)
- **expo-notifications** (notificação local para lead crítico)
- Dark mode automático via `useColorScheme()`

## Estrutura

```
PrevioPLS-Mobile/
├── app/                        # Expo Router file-based routing
│   ├── _layout.tsx             # Root: SafeArea + Stack + bootstrap auth
│   ├── index.tsx               # Redirect baseado em token
│   ├── login.tsx               # POST /v1/auth/login → SecureStore
│   └── (app)/                  # Rotas protegidas (precisam JWT)
│       ├── _layout.tsx         # Guard: redireciona pra /login se sem token
│       ├── leads.tsx           # Lista (GET /v1/leads) — pull-to-refresh
│       └── lead/[id].tsx       # Visão 360 + ações (PATCH /v1/leads/:id)
├── components/
│   ├── LeadCard.tsx
│   ├── PerfilChip.tsx          # Chip colorido por perfil
│   ├── PrioridadeBadge.tsx     # Badge da prioridade do lead
│   └── ActionButtons.tsx       # Botões Agendar / Recusado / Sem contato
├── constants/
│   ├── colors.ts               # Paleta light/dark, Ford blue (#003478)
│   └── perfis.ts               # Labels + cores + inferência perfil←score
├── lib/
│   ├── api.ts                  # axios + interceptor (injeta JWT, captura 401)
│   ├── auth.ts                 # getToken/setSession/clearSession
│   ├── storage.ts              # wrappers tipados SecureStore + AsyncStorage
│   ├── events.ts               # emitter mínimo (evita ciclos store↔api)
│   └── notifications.ts        # setup + helpers expo-notifications
├── store/
│   ├── auth.ts                 # Zustand: token, role, bootstrap, login, logout
│   └── leads.ts                # Zustand: items, fetch, refresh, patchStatus
├── types/
│   └── index.ts                # Lead, Cliente, Veiculo, enums, responses
├── app.json                    # Expo config (plugins: router, secure-store, notifications)
├── package.json
├── tsconfig.json               # Paths: "@/*" → "./*"
├── babel.config.js             # babel-preset-expo + reanimated/plugin
├── expo-env.d.ts               # typed routes + EXPO_PUBLIC_API_URL
├── .env.example
└── README.md
```

## Pré-requisitos

- Node.js 18+
- pnpm / npm / yarn
- Backend PrevioPLS rodando em `http://localhost:5000` — código + instruções em [github.com/Lynnbrosa/challenge-SOA](https://github.com/Lynnbrosa/challenge-SOA)
- Para Android: Android Studio + emulador ou device físico
- Para iOS: Xcode (apenas no macOS) ou Expo Go no iPhone

## Setup

```bash
cd C:\Users\User\PrevioPLS-Mobile
npm install
cp .env.example .env
# ajuste EXPO_PUBLIC_API_URL conforme sua plataforma (ver tabela abaixo)
npm start
```

O `npm start` abre o Metro Bundler. Escolha:
- `a` → Android emulator
- `i` → iOS simulator (macOS)
- Ou escaneie o QR code no Expo Go (device físico)

## Como o app encontra o backend

`EXPO_PUBLIC_API_URL` no `.env` é lido em tempo de build pelo Expo. Cada plataforma enxerga o `localhost` da máquina-host de um jeito diferente:

| Plataforma                                    | EXPO_PUBLIC_API_URL                          |
|-----------------------------------------------|----------------------------------------------|
| Android emulator                              | `http://10.0.2.2:5000`                       |
| iOS simulator (macOS)                         | `http://localhost:5000`                      |
| Device físico (Android/iPhone) no mesmo Wi-Fi | `http://<IP-da-sua-máquina>:5000`            |
| Expo tunnel (`npx expo start --tunnel`)       | URL do túnel exibida no terminal             |

Pra descobrir o IP local:
- Windows: `ipconfig` (procure por "IPv4")
- macOS/Linux: `ifconfig` ou `hostname -I`

Quando rodar no device físico, garanta que:
1. O Spring Boot esteja escutando em `0.0.0.0:5000` (já é o default).
2. O firewall da máquina permita conexão na porta 5000.

## Credenciais de desenvolvimento

Em modo dev (`__DEV__`), o formulário de login já vem pré-preenchido com:

| Email                  | Senha    | Papel     |
|------------------------|----------|-----------|
| `consultor@ford.com`   | `cons123`  | CONSULTOR |
| `admin@ford.com`       | `admin123` | ADMIN     |

O app filtra apenas leads do consultor — admin pode logar mas não tem tela diferenciada nessa entrega.

## Fluxo de uso

### 1. Login

`app/login.tsx` → `useAuthStore.login()` → POST `/v1/auth/login` → `setSession()` grava JWT no `expo-secure-store` (criptografado pelo OS — Keychain no iOS, EncryptedSharedPreferences no Android).

### 2. Lista de leads

`app/(app)/leads.tsx` → `useLeadsStore.fetchLeads()` → GET `/v1/leads?status=aberto&per_page=100`.

A lista vem **já ordenada pelo backend** (CRITICA → ALTA → MEDIA → BAIXA, depois score desc). O app só renderiza na ordem recebida — sem reordenação client-side, evitando inconsistência.

- **Pull-to-refresh** via `RefreshControl`.
- **Cache offline**: a lista é persistida em `AsyncStorage` (`leads:items:v1`) e re-hidrata no boot — funciona sem rede.
- **Notificação push local**: ao detectar um lead novo com `prioridade === 'critica'` que ainda não estava no cache, dispara `Notifications.scheduleNotificationAsync` imediatamente. Não é um push real (sem servidor de push), é uma notificação local — suficiente pra demonstrar o fluxo e o diferencial pedido no PDF.

### 3. Visão 360

`app/(app)/lead/[id].tsx` → GET `/v1/leads/{id}`. Mostra:
- Hero: chip de perfil + score % + status
- Cliente (telefone, email, CPF mascarado, região)
- Veículo (modelo, ano, VIN, data da compra, valor, concessionária)
- Script de abordagem (gerado pelo `MlService` no backend conforme o perfil)
- Observação (preenchida quando o consultor já tomou ação)

### 4. Ação rápida

Botões fixos no rodapé chamam `useLeadsStore.patchStatus(id, status)` → PATCH `/v1/leads/{id}`. Após sucesso:
- Lead some da lista local (se status ≠ aberto).
- Notificação local confirma a ação.
- App volta automaticamente pra lista.

## Interceptor JWT

`lib/api.ts` adiciona dois interceptors no axios:

1. **Request**: lê token do `SecureStore` e injeta `Authorization: Bearer <token>` em todas as requisições. Não usa cache em memória — sempre lê do storage. Mais seguro (token rotacionado é refletido imediatamente).

2. **Response**: se status for **401**, limpa a sessão e emite `auth:expired` num `TinyEmitter` próprio. O `store/auth.ts` escuta esse evento e zera o estado Zustand → o `(app)/_layout.tsx` reage e redireciona pra `/login`. Esse padrão de evento evita o ciclo de imports `api ↔ store/auth`.

## Diferenciais entregues

Pelo PDF da disciplina ("Funcionalidades como notificações, armazenamento local ou integração com sensores serão consideradas diferenciais"):

- **Notificações locais** quando um lead crítico aparece + quando o status é atualizado (`expo-notifications`).
- **Armazenamento seguro do JWT** com criptografia nativa (`expo-secure-store`).
- **Cache offline** dos leads em `AsyncStorage` — a lista de hoje continua acessível sem rede.
- **Dark mode** automático seguindo o tema do sistema operacional.

Ganchos prontos pra futuros diferenciais (não ativados nesta entrega):
- `expo-local-authentication` (Face ID/digital) — bastaria envolver a chamada de `login` numa autenticação biométrica antes de tentar usar o token armazenado.
- `expo-location` — geolocalização do consultor no momento da abordagem.
- `expo-camera` — scanner de placa/QR pra acelerar a busca.

## Comandos úteis

```bash
npm start                   # Metro com seletor de plataforma
npm run android             # já abre no emulador Android
npm run ios                 # abre no simulador iOS (macOS)
npx expo start --tunnel     # túnel pra device em rede separada
npx expo start --clear      # limpa cache do Metro (resolva 99% dos "Unable to resolve")
npx tsc --noEmit            # checagem de tipos sem build
```

## Troubleshooting

**"Network Error" ao tentar logar**
1. Confirme que o backend Spring Boot está respondendo em `http://localhost:5000/health`.
2. Confira o `EXPO_PUBLIC_API_URL` no `.env` (tabela acima).
3. Após editar `.env`, reinicie o Metro com `npx expo start --clear`.

**Notificações não aparecem no emulador iOS**
Notificações funcionam em device físico ou Android emulator. No iOS simulator a entrega é limitada por design da Apple.

**"Unable to resolve module @/..."**
Limpe o cache: `npx expo start --clear`. O alias `@/*` está no `tsconfig.json` e o Metro do Expo SDK 51 entende sem precisar de `babel-plugin-module-resolver`.

**Lead some da lista após PATCH e quero ver de novo**
Filtre por `status=agendado` no backend (ainda não há toggle no app — ganho fácil de UI).

## Mapeamento × User Stories

| US     | O quê                                           | Onde no app                                                |
|--------|--------------------------------------------------|------------------------------------------------------------|
| US04   | JWT + criptografia em repouso                    | `lib/auth.ts` (SecureStore) + interceptor de 401           |
| US05   | Lista diária ordenada por risco                  | `app/(app)/leads.tsx` + ordenação server-side              |
| US06   | Visão 360 consolidada                            | `app/(app)/lead/[id].tsx`                                  |
| US07   | Botões de ação rápida + status no banco          | `components/ActionButtons.tsx` + `useLeadsStore.patchStatus` |
| —      | Notificação para lead crítico                    | `lib/notifications.ts` + detecção em `useLeadsStore.fetchLeads` |
