# CLAUDE.md

Contexto operacional do repositório PrevioPLS. Documento de referência para qualquer contribuição automatizada ou manual. Tudo aqui é decisão tomada, não tópico em aberto.

## Missão

Consolidar os 4 repositórios da challenge Ford FIAP 2026 em um único repositório de produto chamado PrevioPLS, posicionado para a Ford Brasil avaliar e voltar a chamar o time no final do ano. Os 4 repositórios originais ficam congelados (em avaliação acadêmica) e não podem ser modificados. Este repositório é o consolidado público-facing.

Repositórios fonte:

- `https://github.com/Lynnbrosa/challenge-SOA` (backend Java Spring Boot)
- `https://github.com/Lynnbrosa/challenge-Cyber` (security API FastAPI)
- `https://github.com/Lynnbrosa/challenge-IAML` (notebook ML)
- `https://github.com/Lynnbrosa/challenge-Mobile` (app React Native)

## Audiência

Tudo escrito (README, docs, comentários, mensagens de commit) é para a Ford Brasil ler, não para o professor. Tom de produto sério, não TCC.

## Contexto para ler antes de escrever

Já presente no repositório (em `docs/`):

- `docs/pulse-deck.pdf` (apresentação final, 24/05/2026)
- `docs/previopls.archimate` (modelo TOGAF completo, 4 views)

Após a Fase 1 estará também:

- READMEs dos 4 serviços/apps importados
- `docs/threat-model.md` (movido de gateway)
- `docs/ml-report.md` (movido do notebook, ex `relatorio_executivo.md`)

Ler todos antes de gerar conteúdo derivado.

## Estrutura final do repositório

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
│   ├── gateway/                 (subtree de challenge-Cyber)
│   ├── core/                    (subtree de challenge-SOA)
│   └── ml/
│       ├── notebook/            (subtree de challenge-IAML)
│       └── api/                 (novo serviço FastAPI)
├── apps/
│   ├── consultor-mobile/        (subtree de challenge-Mobile)
│   └── admin-web/               (novo Next.js)
├── infra/
│   ├── docker-compose.yml
│   └── deploy/
└── scripts/
    └── build-seed/
```

## Posicionamento dos dois backends

O backend Python (gateway) e o Java (core) não são duplicação, são camadas. Narrativa oficial:

- Gateway (Python/FastAPI): edge de segurança LGPD. Faz TLS termination, valida JWT, aplica rate limit, executa HMAC verification, audita acesso, repassa para o core via rede interna.
- Core (Java/Spring Boot): serviço de domínio. Persiste cliente, classifica via ML, gera leads. Só aceita requisições da rede interna (gateway).

Não reescrever as APIs duplicadas. Apenas reposicionar no `ARCHITECTURE.md` e no compose: gateway escuta em 443 público, core escuta em rede `previopls` interna. Documentar essa decisão como ADR.

## Wiring do modelo ML

O `services/core/...service/MlService.java` hoje é stub SHA-256. O plano é:

1. Criar `services/ml/api/` (FastAPI mínimo) que carrega `ml_model.pkl` exportado do notebook do IAML e expõe `POST /predict`.
2. Trocar o stub do `MlService.java` por chamada REST a `http://ml-api:8000/predict` (rede interna do compose).
3. Manter a assinatura pública do método Java igual: input `ClassificacaoRequest` D0, output `(PerfilCliente, BigDecimal score)`. Toda a refatoração contida nesta classe. Não tocar em Controller ou Service de Cliente.

Contrato do `/predict`:

- Body: `{regiao, modelo, ano, valor_compra, concessionaria_id}` (só features D0)
- Response: `{perfil: "FIEL"|"ABANDONO"|"ESQUECIDO"|"ECONOMICO", score: 0.0..1.0, latency_ms: int}`
- Latência alvo: p95 < 500ms

Validação anti-leakage no boot do ml-api: lançar `RuntimeError` se o pipeline carregado tem feature names contendo tokens banidos (`recency`, `frequency`, `monetary`, `tenure`, `r_`, `f_`, `m_`).

Sobre o dataset Ford real: `vin_share_Desafio_02.xlsx` não está commitada (82MB, .gitignore). O `ml_model.pkl` gerado deve sair do notebook rodado com o dataset Online Retail (proxy metodológico) que está no repo do IAML em `data/`. Documentar isso. Adicionar um script `scripts/retrain-with-ford-data.sh` que aceita o caminho da xlsx Ford via argumento e regera o modelo. Não tentar baixar a xlsx Ford de nenhum lugar.

## Fases de execução

Executar em ordem. Commit após cada fase com mensagem descritiva.

### Fase 1: subtree dos 4 repositórios

```bash
git subtree add --prefix=services/core https://github.com/Lynnbrosa/challenge-SOA main --squash
git subtree add --prefix=services/gateway https://github.com/Lynnbrosa/challenge-Cyber main --squash
git subtree add --prefix=services/ml/notebook https://github.com/Lynnbrosa/challenge-IAML main --squash
git subtree add --prefix=apps/consultor-mobile https://github.com/Lynnbrosa/challenge-Mobile main --squash
```

Após import, mover:

- `services/gateway/threat_model.md` → `docs/threat-model.md`
- `services/ml/notebook/relatorio_executivo.md` → `docs/ml-report.md`
- `services/ml/notebook/scripts/build_seed.py` → `scripts/build-seed/` (manter cópia no notebook também, é dependência dele)

Commit: `chore: import services and apps via subtree`

### Fase 2: README + ARCHITECTURE + BUSINESS_CASE

README.md raiz (não repetir o que está nos READMEs internos, apresentar o produto e rotear):

1. Hero: 1 frase forte do que é PrevioPLS
2. O problema (3 linhas, do deck)
3. A solução (3 linhas)
4. Arquitetura em 1 diagrama Mermaid simplificado (5 a 7 componentes)
5. Stack consolidada (tabela curta)
6. Como rodar localmente: `docker-compose up` na raiz
7. Links: deck, whitepaper, threat model, ml report, business case
8. Estrutura do monorepo (árvore simplificada)
9. Time (ler o slide do deck para pegar os nomes)

ARCHITECTURE.md:

- Diagrama de contexto C4 nível 1 (Mermaid)
- Diagrama de container C4 nível 2 (Mermaid) com gateway, core, ml-api, postgres, mobile, admin-web
- Sequence diagram: fluxo D0 → classificação → lead → notificação consultor
- Fronteiras de trust LGPD (o que é PII, onde é cifrado, onde é mascarado)
- ADRs leves (decisão + contexto + consequência) para:
  - Por que dois backends (gateway/core split)
  - Por que sklearn standalone via FastAPI ao invés de embedar no Java
  - Por que JWT RS256 no edge e HS256 internamente
  - Por que Fernet em PII no gateway e AES-GCM no core (não unificar, é defense in depth)
- Renderizar o `.archimate` em prosa + Mermaid, não embutir o XML.

BUSINESS_CASE.md (esqueleto, não inventar números):

- Seções vazias com placeholders `<<TBD>>`:
  - Mercado endereçável (Anfavea/Fenabrave) `<<TBD: vendas Ford Brasil 2024-2025>>`
  - Receita perdida estimada `<<TBD: ticket médio revisão Ford × % abandono>>`
  - Recuperação via PrevioPLS `<<TBD: % conversão piloto>>`
  - Custo da plataforma `<<TBD: infra Vercel + Render + Neon no piloto, AWS em produção>>`
  - Payback estimado `<<TBD>>`
- Nota explícita no topo: documento em construção, números a preencher com dados públicos antes da próxima apresentação.

Commit: `docs: add root README, ARCHITECTURE and BUSINESS_CASE skeleton`

### Fase 3: docker-compose unificado

Base no `services/gateway/docker-compose.yml` (que já existe), estender:

```yaml
services:
  postgres:        # único, compartilhado, schemas separados por serviço
  gateway:         # FastAPI, expõe 443 via nginx
  core:            # Spring Boot, porta interna 5000
  ml-api:          # FastAPI novo, porta interna 8000
  admin-web:       # Next.js, porta 3000
  nginx:           # já existe no gateway, ajustar para rotear /api/* para o gateway e /* para o admin-web
```

Rede `previopls` interna. Só nginx exposto publicamente. Healthchecks em cada serviço. Depends_on com `condition: service_healthy`.

Mover o compose para `infra/docker-compose.yml` (raiz). Os composes/Dockerfiles dentro de cada serviço continuam funcionando isoladamente também.

Commit: `chore: unified docker-compose with all services`

### Fase 4: services/ml/api

```
services/ml/api/
├── Dockerfile
├── requirements.txt
├── pyproject.toml
├── README.md
├── app/
│   ├── main.py
│   ├── schemas.py
│   ├── predictor.py
│   └── health.py
└── models/
    └── ml_model.pkl
```

Stack: FastAPI, Pydantic v2, joblib, scikit-learn (mesma versão que o notebook usou).

Validação anti-leakage no startup (descrita acima).

Logs JSON via structlog (consistência com gateway).

README do `ml-api/` explica: contrato, como regerar o `ml_model.pkl` a partir do notebook (incluindo `scripts/retrain-with-ford-data.sh`), latência observada localmente.

Em paralelo: editar `MlService.java` do core. Substituir SHA-256 por chamada via Spring `RestClient` (não usar `RestTemplate`, que está deprecated em Boot 3). URL configurável via env `ML_API_URL`, default `http://ml-api:8000`. Timeout 2s. Fallback: se ml-api offline, log warning + retorna perfil default `ESQUECIDO` com score 0.5 (não derruba o request).

Commit: `feat(ml): wire real model via ml-api service`

### Fase 5: apps/admin-web

Stack: Next.js 14+ App Router, Tailwind, shadcn/ui (mencionar no README do app que usa), Recharts.

Páginas:

- `/` redirect para `/dashboard`
- `/login` form mínimo, autentica via gateway `/v1/auth/login`, salva JWT em httpOnly cookie via Next.js API route
- `/dashboard` cards de totais por perfil (chart pizza Recharts) + lista de leads críticos do dia
- `/leads` tabela completa com filtros (prioridade, status, perfil), paginação
- `/leads/[id]` visão 360 (cliente, veículo, script, histórico) + ações (agendar/recusar)
- `/about` arquitetura + métricas ML + links para os docs

Visual: paleta Ford (azul `#003478`, branco, cinzas), tipografia limpa (system stack ou Inter), sem animações exageradas, sem glassmorphism. Profissional. Para a Ford abrir num laptop corporativo, não para impressionar designer.

Env: `NEXT_PUBLIC_API_URL` aponta para o gateway. Default `https://localhost` em dev (aceita cert self-signed).

README do `admin-web/` documenta como rodar, env vars, e como gerar build de produção.

Commit: `feat(admin-web): Next.js dashboard for stakeholder demo`

### Fase 6: deploy config

`infra/deploy/` com specs de provisionamento por provedor. Stack escolhida prioriza free tier sem cartão amarrado:

- Vercel para o admin-web (Next.js).
- Render para os 3 backends (gateway, core, ml-api) via Dockerfile.
- Neon para o Postgres (3 GB free, 2 bases: `previopls_core` e `previopls_gateway`).

Arquivos:

- `vercel-admin-web.md`
- `render-gateway.md`
- `render-core.md`
- `render-ml-api.md`
- `neon-postgres.md`

Documentar no README raiz: gateway em `api.previopls.com.br`, admin-web em `app.previopls.com.br`, core e ml-api privados na rede da Render.

Não executar deploy. Apenas documentar. Deploy real é manual.

Commit: `chore(infra): deploy specs for vercel + render + neon`

### Fase 7: whitepaper

`docs/whitepaper.md`, 6 a 10 páginas em PT-BR, escrito como artigo técnico de startup pitching Ford. Estrutura:

1. Abstract (4 linhas)
2. Problema (com números do deck)
3. Solução (PrevioPLS, posicionamento)
4. Arquitetura (resumo do ARCHITECTURE.md + diagramas)
5. Modelo ML (resumo do ml-report.md + decisão D0-only + anti-leakage)
6. Segurança e LGPD (resumo do threat-model.md)
7. Métricas (preencher com placeholders `<<TBD>>` quando F1 final não tiver sido medido)
8. Business case (preencher com placeholders, referência ao BUSINESS_CASE.md)
9. Roadmap pós-piloto (sprints 3 e 4 do deck + além)
10. Time

Sem em-dashes, sem CAPS, sem linhas decorativas. Voz: técnica e direta.

Commit: `docs: add whitepaper`

## Quality bars

### Estilo de escrita em docs

- Português brasileiro em toda prosa.
- Sem em-dashes. Usar vírgula, parênteses, dois pontos ou ponto final.
- Sem TUDO MAIÚSCULO para ênfase ou label.
- Sem linhas decorativas (`---`, `===`, `***`) exceto separadores de seções markdown padrão.
- Headers em title case ou frase normal, não SHOUTING.
- Voz assertiva sem hype.
- Listas com bullets razoáveis (3 a 7 itens). Listas com 15 itens viram tabela ou texto corrido.

### Estilo de código

- Manter convenção do código existente de cada serviço.
- Java em camelCase, Python em snake_case, TypeScript em camelCase.
- Comentários: manter o idioma já usado em cada serviço (PT no core/gateway, EN no mobile/admin-web é OK).
- Nada de comentário com marcação genérica de origem ou TODO sem contexto.

### Mensagens de commit

- Conventional commits: `feat:`, `fix:`, `chore:`, `docs:`, `refactor:`.
- Em inglês, curto, descritivo. Sem assinaturas extras.

## Anti-patterns

- Não inventar métricas. F1 não medido = "F1 alvo ≥ 0.75, medição final pendente". Não chutar 0.82.
- Não inventar preços, custos, ROI. Usar `<<TBD>>` com nota explicativa.
- Não copiar código entre serviços só para parecer cheio.
- Não criar testes só para ter pasta `tests/`. Teste de verdade ou nada.
- Não adicionar bibliotecas novas sem justificar no README do serviço.
- Não criar releases ou tags.
- Não publicar nada com nome de empresa do time.
- Não incluir dados pessoais do time além dos nomes que já estão no deck.
- Não rodar `git subtree push` (tentaria empurrar para os originais, que estão em avaliação).
- Não tentar baixar `vin_share_Desafio_02.xlsx` de lugar nenhum, ela não está pública.
- Não modificar arquivos dentro de `services/{core,gateway,ml/notebook}` ou `apps/consultor-mobile` exceto quando explicitamente especificado (move de threat-model, swap do MlService).

## Definição de pronto

- 4 repositórios importados via subtree com histórico preservado.
- `docker compose -f infra/docker-compose.yml up` sobe stack completa sem erro.
- Login no admin-web funciona, dashboard mostra os leads do seed.
- `POST /predict` no ml-api retorna perfil real, com latência p95 < 500ms local.
- Core consome ml-api via REST interno, e o `MlService.java` não tem mais SHA-256.
- README raiz, ARCHITECTURE.md, BUSINESS_CASE.md (esqueleto), whitepaper.md escritos.
- Diagramas Mermaid renderizam no GitHub web.
- threat-model.md e ml-report.md movidos para `docs/`.
- Nenhum em-dash em prosa, nenhuma linha decorativa, nenhum CAPS gratuito.
- Primeira impressão ao abrir o repositório: produto, não trabalho de faculdade.
