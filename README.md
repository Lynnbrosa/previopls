# PrevioPLS

Plataforma preditiva de retenção pós-venda. Classifica o comprador no exato momento da compra (D0) para permitir ação comercial antes da primeira revisão, sustentando o VIN Share da rede oficial Ford.

## O problema

A concessionária não sabe, no ato da venda, qual cliente deixará de retornar para revisões. Quando o CRM percebe o abandono, o cliente já criou hábito em oficinas paralelas. Campanhas genéricas tratam fiéis e clientes em risco da mesma forma, desperdiçando margem e perdendo justamente quem é recuperável.

## A solução

PrevioPLS classifica cada novo comprador em um de 4 perfis comportamentais (Fiel, Abandono, Esquecido, Econômico) usando apenas variáveis disponíveis no D0. Quando o perfil é de risco, a plataforma gera um lead priorizado que chega no app do consultor com script comercial específico. A ação acontece antes do gap de manutenção, no janela em que ainda existe relacionamento.

## Arquitetura em uma vista

```mermaid
graph LR
    Fat[Faturamento Ford] -->|HMAC + D0| GW[Gateway FastAPI]
    App[App Consultor<br/>React Native] -->|JWT| GW
    Web[Admin Web<br/>Next.js] -->|JWT| GW
    GW -->|REST interno| Core[Core<br/>Spring Boot]
    Core -->|POST /predict| ML[ml-api<br/>FastAPI + sklearn]
    Core --> DB[(PostgreSQL 16)]
    GW --> DB
```

O Gateway é a borda pública. Termina TLS, valida JWT, aplica rate limit, verifica HMAC nos webhooks de faturamento e repassa para o Core na rede interna. O Core persiste o domínio (cliente, veículo, lead) e delega a classificação ao ml-api. Detalhes em [`ARCHITECTURE.md`](ARCHITECTURE.md).

## Stack consolidada

| Camada                | Tecnologia                                                   |
|-----------------------|--------------------------------------------------------------|
| Edge de segurança     | FastAPI, Pydantic v2, nginx, Fernet, JWT RS256, HMAC-SHA256  |
| Domínio               | Java 21, Spring Boot 3.3, Hibernate, Flyway, AES-256-GCM     |
| Inferência            | Python 3.12, scikit-learn, FastAPI, joblib                   |
| Persistência          | PostgreSQL 16                                                |
| App consultor         | React Native 0.74, Expo SDK 51, TypeScript                   |
| Painel de gestão      | Next.js 14, Tailwind, shadcn/ui, Recharts                    |
| Orquestração local    | Docker Compose                                               |
| Deploy alvo           | Vercel (admin-web) + Render (gateway, core, ml-api) + Neon (Postgres) |

## Como rodar localmente

Pré-requisitos: Docker e Docker Compose v2.

```bash
docker compose -f infra/docker-compose.yml up --build
```

A stack sobe nesta ordem (com healthchecks): PostgreSQL, ml-api, Core, Gateway, Admin Web, nginx. O nginx expõe apenas as portas 80 e 443; todo o resto roda na rede interna `previopls`.

Acessos:

- Painel administrativo: `https://localhost`
- Swagger do Gateway: `https://localhost/docs` (apenas em dev)
- Swagger do Core: `http://localhost:5000/docs` (apenas em dev, fora da rede pública)
- Login padrão de demo: `admin@ford.com / admin123` (admin), `consultor@ford.com / cons123` (consultor)

Aceite o warning de certificado self-signed em dev. Para regenerar segredos do Gateway, consulte [`services/gateway/README.md`](services/gateway/README.md).

## Como o modelo entra em produção

O `MlService` do Core chama `POST /predict` no ml-api por REST interno. O ml-api carrega o `ml_model.pkl` exportado pelo notebook em [`services/ml/notebook/`](services/ml/notebook/) e devolve `(perfil, score, latency_ms)`. A validação anti-leakage roda no boot do ml-api e falha o startup se aparecer qualquer feature pós-venda no pipeline.

O modelo treinado no notebook usa o Online Retail (UCI) como proxy metodológico. Para regerar o `ml_model.pkl` com o dataset Ford real (`vin_share_Desafio_02.xlsx`, não versionada), execute [`scripts/retrain-with-ford-data.sh`](scripts/retrain-with-ford-data.sh) apontando para o arquivo local.

## Documentação

- [`docs/pulse-deck.pdf`](docs/pulse-deck.pdf): apresentação executiva (24/05/2026).
- [`docs/whitepaper.md`](docs/whitepaper.md): visão técnica de 6 a 10 páginas para o stakeholder Ford.
- [`docs/threat-model.md`](docs/threat-model.md): STRIDE em 5 domínios sobre a superfície LGPD.
- [`docs/ml-report.md`](docs/ml-report.md): decisões do modelo, métricas e limitações.
- [`docs/previopls.archimate`](docs/previopls.archimate): modelo TOGAF completo (4 views Open Group ArchiMate 3).
- [`ARCHITECTURE.md`](ARCHITECTURE.md): C4, sequence, ADRs, fronteiras LGPD.
- [`BUSINESS_CASE.md`](BUSINESS_CASE.md): caso de negócio em construção, com placeholders dos números públicos a preencher.

## Estrutura do monorepo

```
previopls/
├── README.md
├── ARCHITECTURE.md
├── BUSINESS_CASE.md
├── CLAUDE.md
├── docs/
│   ├── pulse-deck.pdf
│   ├── whitepaper.md
│   ├── threat-model.md
│   ├── ml-report.md
│   └── previopls.archimate
├── services/
│   ├── gateway/             FastAPI · borda LGPD (TLS, JWT, HMAC, rate limit)
│   ├── core/                Spring Boot · domínio (cliente, lead, classificação)
│   └── ml/
│       ├── notebook/        Jupyter · segmentação + classificação D0
│       └── api/             FastAPI · servidor de inferência para o Core
├── apps/
│   ├── consultor-mobile/    React Native + Expo · app do consultor
│   └── admin-web/           Next.js · painel para gestor de pós-venda
├── infra/
│   ├── docker-compose.yml
│   └── deploy/              Specs por serviço (Vercel, Render, Neon)
└── scripts/
    └── build-seed/          Gerador de seed determinístico a partir do dataset Ford
```

Cada serviço mantém seu próprio README com setup detalhado, variáveis de ambiente e fluxo de uso. Os 4 repositórios originais da challenge ficam congelados em avaliação acadêmica. Este monorepo é a versão de produto.

## Time

Challenge Ford FIAP 2026, turma 2TDSPM.

- Giovanne Charelli Zaniboni Silva
- Leonardo Pasquini Baldaia
- Gustavo Oliveira de Moura
- Lynn Bueno Rosa
