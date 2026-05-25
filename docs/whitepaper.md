# PrevioPLS

## Plataforma preditiva de retenção pós-venda Ford

Whitepaper técnico, versão 1.0, maio de 2026.

## Abstract

PrevioPLS é uma plataforma que classifica o comprador Ford em quatro perfis comportamentais no exato momento da compra (D0) e entrega leads acionáveis ao consultor antes da primeira revisão. O objetivo é elevar o VIN Share da rede oficial agindo no janela em que a evasão ainda é prevenível. Este documento apresenta o problema, a arquitetura, o modelo preditivo, os controles LGPD e o roadmap pós-piloto da solução desenvolvida pela equipe na challenge Ford FIAP 2026.

## 1. O problema

A indústria automotiva brasileira opera com três fragilidades simultâneas no pós-venda:

- 50% de churn pós-garantia segundo o panorama da indústria.
- 30% de abandono na primeira revisão, antes mesmo do consumidor entender a estrutura de manutenção oficial.
- R$ 100 bilhões de mercado anual de reposição, com margem 3 a 5 vezes maior que a margem da venda do veículo, dominado por oficinas independentes.

Esse universo não é exclusivo da Ford. É um problema estrutural de todas as montadoras. A janela crítica é estreita: entre a compra e a primeira revisão, o cliente decide se a rede oficial faz parte da sua rotina ou se a próxima ida ao mecânico será na esquina. A decisão é silenciosa, raramente sinalizada por canal direto. Quando o CRM tradicional detecta o abandono, já é tarde, hábito já criado em oficina paralela.

Os instrumentos atuais não cobrem esse intervalo. CRM tradicional reage a inatividade. Telemática depende de hardware embarcado e gera fricção. Campanhas push genéricas tratam fiéis e clientes em risco do mesmo modo, queimando margem com quem voltaria sozinho e ignorando quem precisava de um empurrão.

## 2. A solução

PrevioPLS preenche essa lacuna com três decisões de produto.

Predição no D0. A classificação acontece no momento exato em que a venda é faturada, antes de qualquer comportamento pós-venda. Usa apenas features disponíveis nesse instante: região, modelo, ano, valor da compra, identificador da concessionária. Essa restrição metodológica é a regra inviolável do projeto, US02.

Quatro perfis comportamentais. Cada cliente é mapeado em Fiel, Abandono, Esquecido ou Econômico. Cada perfil tem um script comercial específico, distribuído ao consultor junto com o lead.

Lead acionável antes do gap. Quando o perfil é Abandono ou Esquecido, o sistema gera automaticamente um lead com prioridade derivada do score e o entrega ao app do consultor responsável. O consultor age no D-X (X dias antes do timing previsto de manutenção) com o script certo, em vez de esperar o vencimento e telefonar para clientes que já estão indo embora.

A vantagem competitiva é tripla. Hardware-agnóstica (funciona com dados que a Ford já possui). Atua via consultor de confiança (não substitui relacionamento, instrumenta). Timing perfeito (aborda antes do cliente decidir sair).

## 3. Arquitetura

O sistema é composto por quatro serviços orquestrados em rede privada, com apenas a borda exposta publicamente.

```
Internet
   │
   ├─ TLS termination
   ├─ Gateway FastAPI (borda LGPD)
   │     · JWT RS256, HMAC, Fernet, rate limit, audit
   │
   ├─ Core Spring Boot 3 (domínio)
   │     · cliente, veiculo, lead, classificacao, AES-256-GCM
   │
   ├─ ml-api FastAPI + sklearn (inferência D0)
   │     · POST /predict, anti-leakage no boot
   │
   └─ PostgreSQL 16 (schemas isolados por serviço)
```

Decisões arquiteturais documentadas como ADRs em [`ARCHITECTURE.md`](../ARCHITECTURE.md), seção 6.

ADR-001 mantém Gateway e Core como camadas distintas em vez de unificá-los. Gateway concentra controles de borda. Core concentra domínio. Defesa em profundidade real, com duas implementações independentes de validação e dois algoritmos de criptografia em PII.

ADR-002 isola o motor de inferência em FastAPI standalone, fora da JVM do Core. Reprocessar um modelo é apenas substituir o pickle e subir uma nova versão do ml-api. O Core ignora qual algoritmo está rodando.

ADR-003 separa JWT RS256 na borda (clientes externos) de HS256 internamente (Gateway para Core). Comprometer um vetor não compromete o outro. Rotação independente, segredos não compartilhados.

ADR-004 cifra PII em duas camadas. Fernet no Gateway. AES-256-GCM no Core via JPA AttributeConverter. Vulnerabilidade em uma das duas bibliotecas não compromete a outra camada.

O fluxo principal D0 está descrito em sequence diagram completo em [`ARCHITECTURE.md`](../ARCHITECTURE.md), seção 3. Em resumo: faturamento Ford emite o D0 assinado via HMAC, Gateway valida e repassa ao Core, Core persiste o cliente cifrado e chama o ml-api, ml-api devolve perfil e score, Core grava o lead com script comercial e dispara notificação ao consultor responsável.

## 4. Modelo preditivo

O motor de classificação é uma pipeline scikit-learn empacotada em FastAPI. Contrato simples:

```
POST /predict
  body  → {regiao, modelo, ano, valor_compra, concessionaria_id}
  resp  → {perfil, score, latency_ms}
```

Apenas 5 features D0 entram no input. O pipeline carregado é validado no boot do ml-api: feature names cruzadas contra uma lista de tokens banidos (`recency`, `frequency`, `monetary`, `tenure`, `r_`, `f_`, `m_`). Se algum aparecer, o boot lança erro e o container morre. As classes emitidas são validadas contra o contrato `{FIEL, ABANDONO, ESQUECIDO, ECONOMICO}` pela mesma razão. Não há janela operacional em que um modelo com leak possa servir requests.

O notebook em [`services/ml/notebook/`](../services/ml/notebook/) trabalha em duas frentes metodológicas. A primeira faz segmentação não-supervisionada com RFM completo (Recency, Frequency, Monetary), AOV, UniqueProducts e Tenure, comparando K-Means, DBSCAN e Hierarchical. K-Means é escolhido por cobertura total, silhouette competitivo e reprodutibilidade em produção. Os clusters resultantes são mapeados aos 4 perfis Ford via heurísticas explícitas sobre as medianas R/F/M/AOV, nunca como "Cluster 0/1/2".

A segunda frente é a classificação supervisionada D0. Três modelos disputaram a vaga via GridSearchCV (5-fold estratificado, F1 macro como métrica de seleção): Logistic Regression, Random Forest e XGBoost.

Performance alvo. F1 macro maior ou igual a 0.75 no dataset Ford. Medição final pendente até o dataset oficial (`vin_share_Desafio_02.xlsx`) entrar no pipeline. O notebook foi desenvolvido com o dataset Online Retail (UCI) como proxy metodológico: cada `CustomerID` representa um comprador, RFM cobre o comportamento pós-venda e features da primeira invoice simulam D0. O método é idêntico ao que será aplicado ao dataset Ford. O script [`scripts/retrain-with-ford-data.sh`](../scripts/retrain-with-ford-data.sh) regera o modelo apontando para a xlsx Ford local.

Latência alvo. P95 abaixo de 500 ms na inferência. Em piloto local, com Logistic Regression e amostras D0 pequenas, ficamos em ordem de unidades de milissegundo. Modelos pesados (XGBoost com muitas árvores) ainda ficam folgados dentro do envelope.

Interpretabilidade. Feature importance nativa e SHAP global respondem ao Art. 20 da LGPD (direito à explicação): por que esse cliente foi marcado como Abandono. A revisão humana é mantida pelo PATCH manual de status do lead pelo consultor.

## 5. Segurança e LGPD

O treatment STRIDE completo está em [`docs/threat-model.md`](threat-model.md), cobrindo cinco domínios: validação de entrada, autenticação e autorização, proteção de APIs, dados e privacidade, logs e auditoria. Resumo dos controles principais.

Borda. TLS 1.2 ou 1.3 obrigatório, HSTS preload, Content-Security-Policy explícita, rate limit em dois níveis (nginx e slowapi). HMAC-SHA256 com janela de 5 minutos protege o webhook crítico `POST /v1/clientes` contra tampering de body, único endpoint que entra PII no sistema.

Identidade. JWT RS256 assimétrico na borda (chave privada em arquivo no piloto, alvo KMS em produção). Access token de 15 min, refresh token de 7 dias com rotação e denylist. bcrypt cost 12 para senhas. Lockout após 5 falhas em 60 s, 15 min de bloqueio.

PII. CPF, email e telefone cifrados em duas camadas independentes. Fernet no Gateway com `cpf_hash` HMAC para lookup sem decifrar. AES-256-GCM no Core via `JPA AttributeConverter`, transparente ao código de negócio. Mascaramento em todas as responses, todos os logs e todos os dashboards via `pii_masking_processor` do structlog. Pseudonimização irreversível para datasets de ML e BI.

Retenção. Coluna `clientes.retencao_ate` e `retention_service.anonymize_expired` cobrem o Art. 16 da LGPD: PII substituída por pseudônimo após 5 anos, mantendo perfil e score para estatística agregada.

Auditoria. Tabela `audit_logs` registra 13 ações cobertas (LOGIN_SUCCESS, LOGIN_FAILED, LOGIN_LOCKED, CLIENTE_CREATED, LEAD_CREATED, LEAD_PATCHED, UNAUTHORIZED_ACCESS, FORBIDDEN_ACCESS, SIGNATURE_REJECTED, MASS_QUERY_DETECTED, entre outras). Cada evento carrega `request_id`, `actor_id`, `remote_ip`, `user_agent`, `jti`. Endpoint admin em `/v1/admin/audit-log` para o DPO consultar a trilha.

Gaps assumidos e endereçáveis. Rate limit em memória (não distribuído) suficiente para single replica, vira Redis distribuído quando o piloto crescer. Chaves Fernet em filesystem viram KMS/HSM em produção. Cert self-signed no nginx vira Let's Encrypt em domínio público.

## 6. Métricas

Performance do modelo D0. F1 macro alvo maior ou igual a 0.75. `<<TBD: F1 medido no dataset Ford>>`. Para um problema multiclasse com sinais D0 puros (sem histórico), 0.75 a 0.85 é o teto pragmático, dado que a maior parte da variância do comportamento de retenção se manifesta DEPOIS da compra. O modelo não precisa ser perfeito; precisa ser melhor que a regra de negócio anterior (que era zero, nenhuma classificação no D0).

Latência. P95 abaixo de 500 ms na inferência ml-api. `<<TBD: percentis medidos no piloto Ford>>`. Em desenvolvimento local com Logistic Regression: ordens de unidades de milissegundo.

Negócio. Quatro KPIs do piloto, descritos em [`docs/ml-report.md`](ml-report.md), seção 7:

- Conversão de risco. Percentual de leads classificados como `ABANDONO` ou `ESQUECIDO` que efetivamente agendaram após abordagem pelo consultor. `<<TBD>>`.
- Impacto direto no VIN Share regional. Comparação em janela de 12 meses entre concessionárias com e sem PrevioPLS habilitado. `<<TBD>>`.
- Tempo de resposta do consultor. Latência entre criação do lead crítico e primeira ação registrada. `<<TBD>>`.
- Adoção operacional. Leads fechados por consultor por dia útil, distribuídos entre `agendado`, `recusado` e `sem-contato`. `<<TBD>>`.

## 7. Caso de negócio

O caso de negócio está estruturado em [`BUSINESS_CASE.md`](../BUSINESS_CASE.md). Resumo dos eixos.

Mercado endereçável. Vendas anuais Ford Brasil em janela 2024 a 2025 `<<TBD>>`. Frota Ford ativa elegível para revisão na rede oficial `<<TBD>>`.

Receita perdida hoje. Função do percentual de abandono pós-venda observado na indústria (30% na 1ª revisão, 50% pós-garantia) cruzado com ticket médio de revisão na rede oficial `<<TBD>>`.

Recuperação via PrevioPLS. Hipótese de elevação da taxa de retorno em janela mensurável. Cenário pessimista 10%, base 20%, otimista 35%. Ganho líquido anual `<<TBD>>` por cenário.

Custo da plataforma. Free tier (Vercel + Render + Neon) em piloto inicial. Após piloto, migração para tier pago (`<<TBD>>` por mês) ou AWS gerenciado (`<<TBD>>` por mês) conforme volume.

Payback. `<<TBD>>`. Função de quanto da receita retida na primeira revisão se propaga para revisões subsequentes.

Os números absolutos serão preenchidos com dados públicos (Anfavea, Fenabrave, ABLA, relatórios financeiros Ford) antes da próxima apresentação ao stakeholder. A estrutura está fixa.

## 8. Roadmap pós-piloto

Sprint 3, melhorias durante a janela de piloto:

- A/B Test de Scripts. Validação de eficácia comercial por perfil. Comparar conversão entre script A e script B no mesmo perfil em concessionárias controle.
- Drift Monitoring. Teste KS em features D0 mensal para detectar quando o modelo precisa retreinar.
- Refresh Tokens. Segurança avançada no Backend Java, paridade com o esquema já implementado no Gateway Python.

Sprint 4, expansão após validação do piloto:

- SDK Ford App. Integração direta no app do cliente final Ford, abrindo canal proativo ao próprio comprador além do consultor.
- Requalificação IA. Modelo de Reinforcement Learning pós-agendamento, aprendendo com o resultado da abordagem para recalibrar scripts e timing.
- Expansão Regional. Piloto em 10 novas praças, validando o modelo em distribuições regionais distintas.

Além do roadmap declarado no deck, o time identifica três frentes naturais de evolução:

- Enriquecimento de features D0 com sociodemográfico do CEP e score de crédito (apenas com base legal e consentimento explícito), elevando o teto pragmático do F1.
- Endpoint admin `/admin/clientes/{id}/explain` com SHAP local por cliente, atendendo solicitações individuais do Art. 20 da LGPD.
- Migração do rate limit em memória para Redis distribuído, viabilizando múltiplas réplicas do Gateway sob ataque.
