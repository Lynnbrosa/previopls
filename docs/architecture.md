# Arquitetura — PrevioPLS Backend

## Diagrama de componentes (alto nível)

```mermaid
flowchart TB
    %% ============= ATORES =============
    subgraph Atores
        Admin([Admin Concessionária])
        Consultor([Consultor de Serviços])
    end

    %% ============= CLIENTES DE API =============
    subgraph Clientes_de_API["Clientes da API"]
        AppMobile["App Mobile RN/Expo<br/>(Consultor)"]
        AdminUI["Painel Admin / Sistema de Faturamento<br/>(envia D0 da compra)"]
    end

    %% ============= GATEWAY =============
    subgraph Borda["Borda (Nginx / ALB)"]
        TLS["TLS 1.2+ &<br/>Rate Limiting"]
    end

    %% ============= BACKEND =============
    subgraph Backend["PrevioPLS Backend (Spring Boot 3 / Java 21)"]
        direction TB
        Controllers["controller/<br/>(REST controllers)<br/>GET /health · /version<br/>POST /v1/auth/login<br/>POST /v1/clientes<br/>GET /v1/leads<br/>GET /v1/leads/:id<br/>PATCH /v1/leads/:id"]
        Security["Spring Security 6<br/>JwtAuthFilter +<br/>@PreAuthorize (RBAC)"]
        Services["service/<br/>Auth · Cliente · Lead · Jwt"]
        MlService["MlService<br/>(motor preditivo)"]
        Repos["repository/<br/>JpaRepository (Spring Data)"]
        Entities["entity/<br/>(JPA / Hibernate)"]
        ExcHandler["@RestControllerAdvice<br/>GlobalExceptionHandler<br/>(sem stack trace)"]

        Controllers --> Security
        Security --> Services
        Services --> Repos
        Services --> MlService
        Repos --> Entities
        Controllers -.erros.-> ExcHandler
    end

    %% ============= DATA =============
    subgraph Dados
        DB[("PostgreSQL 14+<br/>usuarios · clientes · veiculos · leads")]
        Flyway["Flyway<br/>(V1__initial_schema.sql)"]
    end

    %% ============= FLUXOS =============
    Admin --> AdminUI
    Consultor --> AppMobile

    AppMobile -->|HTTPS + Bearer JWT| TLS
    AdminUI -->|HTTPS + Bearer JWT| TLS
    TLS --> Controllers

    Entities -->|SQL via Hibernate| DB
    Flyway -.versiona.-> DB

    %% Caminho crítico US01: D0 → classificação → lead
    MlService -.classifica D0.-> Services
    Services -.gera lead<br/>se perfil de risco.-> Repos

    classDef ext fill:#1a4fa3,stroke:#0a2f6b,color:#fff
    classDef svc fill:#003478,stroke:#001f4d,color:#fff
    classDef data fill:#1e7e34,stroke:#0c5022,color:#fff
    class AppMobile,AdminUI ext
    class Controllers,Security,Services,MlService,Repos,Entities,ExcHandler svc
    class DB,Flyway data
```

## Sequence — POST /v1/clientes (cadastro D0 da compra)

```mermaid
sequenceDiagram
    autonumber
    participant U as Sistema Faturamento (Admin)
    participant C as ClienteController
    participant S as ClienteService
    participant M as MlService
    participant CR as ClienteRepository
    participant VR as VeiculoRepository
    participant LR as LeadRepository
    participant DB as PostgreSQL

    U->>C: POST /v1/clientes (JSON D0)
    C->>C: @Valid (Jakarta Validation)<br/>JWT + hasRole('ADMIN')
    C->>S: cadastrarCompra(request)
    S->>CR: existsByCpf
    CR->>DB: SELECT
    S->>VR: existsByVin
    VR->>DB: SELECT
    S->>CR: save(Cliente)
    CR->>DB: INSERT
    S->>VR: save(Veiculo)
    VR->>DB: INSERT
    S->>M: classificar(features_D0)
    M-->>S: ResultadoClassificacao(perfil, score)
    alt perfil em {ABANDONO, ESQUECIDO}
        S->>LR: save(Lead com prioridade derivada)
        LR->>DB: INSERT
    end
    Note over S,DB: @Transactional faz commit no retorno
    S-->>C: ClienteCreatedResponse(cliente, leadId, perfil, score)
    C-->>U: 201 Created
```

## Sequence — GET /v1/leads + PATCH /v1/leads/:id (app mobile)

```mermaid
sequenceDiagram
    autonumber
    participant App as App Mobile
    participant LC as LeadController
    participant LS as LeadService
    participant LR as LeadRepository
    participant DB as PostgreSQL

    App->>LC: GET /v1/leads?prioridade=alta&status=aberto
    LC->>LC: JWT + hasAnyRole('CONSULTOR','ADMIN')
    LC->>LS: listar(prioridade, status, page, perPage)
    LS->>LR: findFiltered(...)
    LR->>DB: SELECT leads JOIN clientes JOIN veiculos<br/>ORDER BY prioridade, score DESC
    LR-->>LS: Page<Lead>
    LS-->>LC: LeadListResponse
    LC-->>App: 200 OK (paginado)

    Note over App,DB: Consultor abre detalhe e registra resultado

    App->>LC: GET /v1/leads/{id}
    LC->>LS: obter(id)
    LS->>LR: findByIdWithDetails(id)
    LR-->>LS: Lead com cliente+veiculo
    LS-->>LC: LeadDetailResponse
    LC-->>App: 200 OK

    App->>LC: PATCH /v1/leads/{id} {status:"agendado"}
    LC->>LS: atualizarStatus(id, request)
    LS->>LR: findByIdWithDetails(id) (no Transactional → dirty checking)
    LS->>LS: lead.setStatus(AGENDADO)
    Note over LS,DB: @Transactional → flush no return → UPDATE
    LS-->>LC: LeadDetailResponse
    LC-->>App: 200 OK
```

## Modelo de dados (ER)

```mermaid
erDiagram
    CLIENTES ||--o{ VEICULOS : possui
    CLIENTES ||--o{ LEADS : gera
    VEICULOS ||--o{ LEADS : referencia

    USUARIOS {
        uuid id PK
        string nome
        string email UK
        string senha_hash
        enum papel "ADMIN|CONSULTOR"
        timestamp criado_em
    }
    CLIENTES {
        uuid id PK
        string nome
        string cpf UK
        string email
        string telefone
        string regiao
        enum perfil "FIEL|ABANDONO|ESQUECIDO|ECONOMICO"
        double score_risco
        timestamp criado_em
        timestamp classificado_em
    }
    VEICULOS {
        uuid id PK
        uuid cliente_id FK
        string modelo
        string versao
        int ano
        string vin UK
        date data_compra
        numeric valor_compra
        string concessionaria_id
    }
    LEADS {
        uuid id PK
        uuid cliente_id FK
        uuid veiculo_id FK
        double score_risco
        enum prioridade "BAIXA|MEDIA|ALTA|CRITICA"
        enum status "ABERTO|AGENDADO|RECUSADO|SEM_CONTATO"
        text script_oferta
        text observacao
        timestamp criado_em
        timestamp atualizado_em
    }
```

## Camadas SOA — responsabilidades

| Camada           | Responsabilidade                                                    | Onde                                              |
|------------------|---------------------------------------------------------------------|---------------------------------------------------|
| **Apresentação** | Roteamento HTTP, validação (`@Valid` + Jakarta), serialização DTO   | `controller/`, `dto/`                             |
| **Serviço**      | Regra de negócio, orquestração, transações (`@Transactional`)        | `service/` (Auth, Cliente, Lead, Ml, Jwt)         |
| **Dados**        | Acesso ao banco via Spring Data JPA — sem regra de negócio          | `repository/`, `entity/`                          |
| **Infra**        | Security (JWT, RBAC), CORS, OpenAPI, conversão de enums, erro global| `config/`, `exception/`                           |

A separação garante:
- **Reuso**: `LeadRepository.findFiltered` é usado pelo `GET /v1/leads` e pode ser reusado em jobs de relatório.
- **Testabilidade**: services dependem de interfaces `JpaRepository` e são testados isoladamente com Mockito (ver `src/test/java/com/previopls/service/ClienteServiceTest.java`).
- **Substituibilidade**: trocar Postgres por outro banco JPA não afeta controllers/services.
- **Versionamento de contrato**: endpoints de negócio ficam sob `/v1/`; mudanças incompatíveis podem coexistir em `/v2/` sem quebrar o app mobile já distribuído.
- **Observabilidade**: `/health` (com sonda no banco via `JdbcTemplate`) e `/version` ficam fora do versionamento — alvo de k8s probes, ALB health checks e dashboards.
