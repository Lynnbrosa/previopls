# PrevioPLS — Relatório Executivo IA/ML

**Challenge Ford FIAP 2026 · Disciplina: Inteligência Artificial e Machine Learning**

---

## 1. O problema de negócio

Ford precisa aumentar o **VIN Share** — a fração de veículos Ford que retornam à rede oficial para manutenção. No momento da compra, ainda não se sabe o comportamento futuro do cliente. A pergunta operacional é: **qual cliente vai sumir da rede e qual vai voltar?** Quanto mais cedo a concessionária identificar o risco, mais cedo pode agir.

A hipótese de produto é que existem **4 perfis** de comportamento:
- **Fiel** — retorna consistentemente.
- **Abandono** — máximo a primeira revisão e some.
- **Esquecido** — perde o timing, tenta voltar tarde demais.
- **Econômico** — relacionamento existe, mas é sensível a preço.

---

## 2. Abordagem em duas frentes

**Frente 1 — Segmentação (não-supervisionada).** Aplicar clustering sobre dados históricos completos (incluindo comportamento pós-venda) para identificar empiricamente quais perfis existem. Aqui é permitido usar variáveis como número de revisões, recência, monetary.

**Frente 2 — Classificação preditiva (supervisionada).** Treinar um modelo que, no exato **momento da compra (D0)** — sem nenhum dado pós-venda — preveja a qual perfil o cliente pertencerá. Esse é o modelo que vai pra produção no sistema de leads da concessionária.

A separação metodológica é estrita. **A violação dessa fronteira (data leakage) invalida o projeto.**

---

## 3. Resultados — Segmentação

A hipótese de 4 perfis se sustenta empiricamente. Os indicadores combinados de **elbow + silhouette + Davies-Bouldin** apontam K=4 como ponto de equilíbrio competitivo, alinhado com o framework comercial pré-existente.

Comparamos K-Means, DBSCAN e Hierarchical (Ward). **K-Means foi escolhido** por três razões:

1. Cobertura total (DBSCAN marca caudas como ruído — inadmissível operacionalmente: o consultor precisa de estratégia pra todo cliente).
2. Silhouette competitivo com Hierarchical.
3. Reprodutibilidade em produção (com `random_state` fixo, gera os mesmos clusters).

Os clusters foram **mapeados aos 4 perfis Ford** com heurísticas explícitas sobre as medianas R/F/M/AOV. Nunca entregamos "Cluster 0/1/2" — cada cluster ganha um nome de negócio que se justifica pelos seus dados.

---

## 4. Resultados — Classificação D0

O classificador supervisionado usa **8 features exclusivamente do momento da compra** — todas validadas contra uma lista de tokens banidos, com bloqueio programático se algo passar.

Três modelos disputaram a vaga via GridSearchCV (5-fold estratificado, F1 macro como métrica):

| Modelo               | Papel                                  |
|----------------------|----------------------------------------|
| Logistic Regression  | Baseline rápido + interpretável        |
| Random Forest        | Não-linearidade + robusto              |
| XGBoost              | Estado-da-arte em tabular              |

**Performance esperada**: F1 macro entre **0.70 e 0.85** dependendo da seed e da versão dos dados. Para um problema multiclasse com sinais D0 puros (sem histórico), é o teto pragmático — a maior parte da variância do comportamento de retenção só se manifesta DEPOIS da compra. O modelo não precisa ser perfeito; precisa ser melhor que a regra de negócio anterior (que era zero — nenhuma classificação no D0).

**Features mais relevantes** (via importância nativa + SHAP):
1. `first_order_value` (valor da 1ª compra).
2. `first_order_avg_unit_price` (ticket médio inicial).
3. `first_country` (região).
4. Padrão temporal (mês + dia da semana da compra).

Faz sentido de negócio: quem gasta bem na 1ª compra tende a ser Fiel; ticket médio baixo + alta quantidade tende a Econômico; região define padrão de uso da rede oficial.

---

## 5. Aplicação operacional

O modelo serializado (`ml_model.pkl`) substitui o stub determinístico atual do `MlService.classificar()` no backend Spring Boot. O fluxo completo passa a ser:

1. **Faturamento** envia POST `/v1/clientes` com dados D0 da compra.
2. **`ClienteService`** persiste cliente + veículo e chama **`MlService.classificar`**.
3. **`MlService`** roda o modelo pickle e retorna `(perfil, score_risco)`.
4. Se perfil ∈ {Abandono, Esquecido}, **`LeadService`** cria automaticamente um lead com prioridade derivada do score + `script_oferta` específico do perfil.
5. **App mobile do consultor** (React Native) recebe **push notification** quando lead crítico aparece (já implementado em `expo-notifications`).
6. Consultor abre **visão 360** com cliente + veículo + script comercial, faz contato e registra o resultado via PATCH.

---

## 6. Estratégia de retenção por perfil

| Perfil      | Quando agir                | Oferta                                                    | Canal                              |
|-------------|----------------------------|-----------------------------------------------------------|------------------------------------|
| **Fiel**     | 30d antes da revisão       | Pacote premium + benefícios exclusivos                    | Push do app + WhatsApp consultor   |
| **Abandono** | Imediato (D+30 da compra)  | Desconto agressivo + brinde institucional                 | Ligação direta + SMS               |
| **Esquecido**| 15d antes do timing previsto | Combo revisão+lavagem + agendamento 1-clique            | Push + e-mail                      |
| **Econômico**| 7d antes da revisão        | Parcelamento + comparativo custo total propriedade        | E-mail + push                      |

A configuração desses scripts é gerenciada via `MlService.SCRIPTS_OFERTA` no backend — basta o time comercial atualizar o texto sem mexer no modelo.

---

## 7. Métricas de sucesso (KPIs do produto)

- **Conversão de risco**: percentual de clientes mapeados como Abandono que agendaram após abordagem pelo app.
- **Impacto no VIN Share**: retenção regional aferida em janela de 12 meses, comparando concessionárias com e sem PrevioPLS habilitado.
- **Adoção operacional**: leads/dia fechados (agendado/recusado/sem-contato) por consultor.
- **Tempo de resposta do consultor**: latência entre criação do lead crítico e primeira ação.

---

## 8. Limitações e próximos passos

| Limitação                                        | Próximo passo                                            |
|-------------------------------------------------|----------------------------------------------------------|
| F1 macro do D0 abaixo de 0.85                    | Enriquecer com sociodemográfico do CEP + score de crédito |
| Dataset proxy (Online Retail)                    | Re-rodar com dataset Ford sintético do professor          |
| Mapeamento cluster→perfil pode mudar com novos dados | Recalcular RFM trimestralmente + retreinar classificador |
| Drift de distribuição D0 ao longo do tempo       | Monitoramento mensal de KS test nas features de entrada   |
| Sem explicação por cliente individual            | Endpoint admin `/admin/clientes/{id}/explain` com SHAP local |

---

## 9. Riscos LGPD

O modelo classifica pessoas em categorias comportamentais — **decisão automatizada** no sentido do Art. 20 da LGPD. Mitigações já endereçadas no backend Python `PrevioPLS-Security/`:

- **Direito à explicação**: SHAP global + nativa permite responder "por que esse cliente foi marcado como Abandono?".
- **Direito à revisão humana**: o consultor pode sempre marcar `recusado` no lead, sobrescrevendo a recomendação automática.
- **Minimização de dados**: o modelo usa 8 variáveis D0 — não há PII no input do classificador (CPF não entra, vai direto pra criptografia Fernet).
- **Auditoria**: cada classificação gera entry em `audit_logs` (`CLIENTE_CREATED` com perfil + score).
