# Caso de Negócio

> Documento em construção. Os números marcados com `<<TBD>>` devem ser preenchidos com dados públicos (Anfavea, Fenabrave, ABLA, relatórios financeiros Ford) antes da próxima apresentação para a Ford. A estrutura abaixo está fixa; só os valores variam.

## 1. Premissa do negócio

PrevioPLS aumenta a probabilidade de o cliente Ford retornar à rede oficial para a primeira revisão, agindo no janela em que o vínculo emocional com a compra ainda é alto e nenhum hábito com oficina paralela foi estabelecido. O caso de negócio mede esse delta em receita retida na rede oficial, não em vendas de veículos novos.

## 2. Mercado endereçável

Universo de veículos novos Ford no Brasil, anuais.

| Indicador                                                | Valor              | Fonte           |
|----------------------------------------------------------|---------------------|------------------|
| Vendas anuais Ford Brasil, 2024 a 2025                   | `<<TBD>>`           | Fenabrave        |
| Frota Ford ativa elegível para revisão na rede oficial   | `<<TBD>>`           | Anfavea          |
| Ticket médio de revisão na rede oficial                  | `<<TBD>>`           | benchmark Ford   |
| Margem média por revisão na rede oficial                 | `<<TBD>>`           | benchmark Ford   |

## 3. Receita perdida hoje

A perda atual é função do percentual de abandono pós-venda observado na indústria automotiva brasileira.

| Indicador                                                | Valor                      | Origem               |
|----------------------------------------------------------|-----------------------------|-----------------------|
| Churn pós-garantia, indústria                            | 50% (deck)                  | apresentação interna  |
| Abandono na primeira revisão, indústria                  | 30% (deck)                  | apresentação interna  |
| Receita não capturada por cliente perdido na 1ª revisão  | `<<TBD: ticket médio Ford>>` | a calcular            |
| Volume estimado de revisões perdidas por ano             | `<<TBD>>`                   | venda anual × 30%     |
| Receita anual perdida na rede oficial                    | `<<TBD>>`                   | volume × ticket       |

## 4. Recuperação via PrevioPLS

A hipótese é que o lead proativo, com script comercial específico por perfil, eleva a taxa de retorno em uma janela mensurável. O piloto medirá o delta concreto. Antes do piloto, usamos uma faixa conservadora como referência.

| Cenário                              | Conversão dos leads de risco | Ganho líquido anual |
|--------------------------------------|------------------------------|------------------------|
| Pessimista                           | `<<TBD: 10%>>`               | `<<TBD>>`              |
| Base                                 | `<<TBD: 20%>>`               | `<<TBD>>`              |
| Otimista                             | `<<TBD: 35%>>`               | `<<TBD>>`              |

A janela do ganho líquido inclui a primeira revisão e as duas seguintes, dado que cliente retido na primeira tende a manter a rede pelo menos até o fim da garantia. O modelo de ganho é refinado no whitepaper.

## 5. Custo da plataforma

| Componente                                       | Custo mensal       | Premissa                     |
|--------------------------------------------------|---------------------|-------------------------------|
| Infra cloud para piloto (Vercel + Render + Neon)  | `<<TBD>>`           | 4 serviços + banco gerenciado, free tier no piloto inicial |
| Infra cloud em produção em escala nacional       | `<<TBD>>`           | EKS + RDS + ALB + S3          |
| Operação do modelo (retreino trimestral)         | `<<TBD>>`           | jornada do time de IA         |
| Suporte operacional ao consultor                 | `<<TBD>>`           | suporte L1 + materiais        |
| Total mensal estimado em piloto                  | `<<TBD>>`           | soma                          |

Os valores absolutos serão preenchidos a partir do dimensionamento de carga real (volume D0 por concessionária × frequência) que apenas o piloto produz com confiança.

## 6. Payback e retorno

| Indicador                                | Valor             |
|------------------------------------------|--------------------|
| Investimento inicial (piloto)            | `<<TBD>>`          |
| Receita retida mensal cenário base       | `<<TBD>>`          |
| Payback estimado                         | `<<TBD>>`          |
| Retorno em 24 meses                      | `<<TBD>>`          |

O payback é função de quanto da receita retida na primeira revisão se propaga para revisões subsequentes. O whitepaper detalha a cadeia de impacto, ver [`docs/whitepaper.md`](docs/whitepaper.md).

## 7. Métricas operacionais do piloto

Independente dos números absolutos, o piloto medirá com confiança quatro métricas que estabelecem o caso de negócio real.

- Taxa de conversão de risco. Percentual de clientes classificados como `ABANDONO` ou `ESQUECIDO` que efetivamente agendaram após abordagem pelo app.
- Impacto direto no VIN Share regional. Comparação 6 a 12 meses entre concessionárias com e sem PrevioPLS habilitado.
- Tempo de resposta do consultor. Latência entre criação do lead crítico e primeira ação registrada.
- Adoção operacional. Leads fechados por consultor por dia útil, com distribuição entre `agendado`, `recusado` e `sem-contato`.

## 8. Riscos do caso de negócio

| Risco                                                       | Probabilidade  | Impacto       | Mitigação                                                                |
|--------------------------------------------------------------|----------------|---------------|---------------------------------------------------------------------------|
| Baixa adoção pelo consultor                                 | Média          | Alto          | UX já pensado para o consultor (app nativo, notificação local, 1 toque para ação) |
| Modelo D0 com F1 abaixo do alvo                              | Média          | Médio         | Estratégia por perfil tolera ruído porque a ação é proativa, não punitiva |
| Multas LGPD por incidente em PII                             | Baixa          | Alto          | Threat model STRIDE coberto, ver [`docs/threat-model.md`](docs/threat-model.md) |
| Resistência regulatória ao uso de decisão automatizada      | Baixa          | Médio         | SHAP global, revisão humana sempre presente via PATCH do consultor       |
| Variação do ticket médio de revisão entre regiões            | Alta           | Baixo         | Modelo de ganho calculado por região, não como média nacional única       |
