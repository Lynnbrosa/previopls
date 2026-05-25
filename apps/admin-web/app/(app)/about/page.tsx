export default function AboutPage() {
  return (
    <div className="space-y-10">
      <header>
        <p className="eyebrow">Sobre a plataforma</p>
        <h1 className="mt-3 text-4xl font-bold tracking-tight text-slate-900">PrevioPLS</h1>
        <div className="ford-rule mt-4" />
        <p className="mt-6 max-w-3xl text-base leading-relaxed text-slate-700">
          Plataforma preditiva de retenção pós-venda Ford. Classifica cada novo comprador no exato momento da
          compra e entrega leads acionáveis ao consultor antes da primeira revisão, sustentando o VIN Share da
          rede oficial.
        </p>
      </header>

      <section className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="card">
          <div className="card-header">
            <p className="eyebrow">Arquitetura</p>
          </div>
          <div className="card-body space-y-3 text-sm leading-relaxed text-slate-700">
            <p>
              Quatro serviços. Gateway FastAPI faz a borda de segurança LGPD, Core Spring Boot persiste o domínio,
              ml-api roda a inferência scikit-learn e este painel coordena o ciclo de vida dos leads.
            </p>
            <p>
              Documentação completa em <code className="rounded-sm bg-slate-100 px-1.5 py-0.5 text-xs">ARCHITECTURE.md</code>:
              C4 nível 1 e 2, sequence do fluxo D0 e quatro ADRs detalhando as decisões arquiteturais sensíveis.
            </p>
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <p className="eyebrow">Modelo preditivo</p>
          </div>
          <div className="card-body space-y-3 text-sm leading-relaxed text-slate-700">
            <p>
              Cinco features D0 puras: região, modelo, ano, valor da compra, concessionária. Nenhuma variável
              pós-venda entra no input, em respeito à US02. O servidor de inferência valida essa restrição no boot.
            </p>
            <p>
              Alvo: F1 macro ≥ 0,75 (medição final pendente para o dataset Ford). Latência alvo p95 menor que 500 ms.
              Relatório em <code className="rounded-sm bg-slate-100 px-1.5 py-0.5 text-xs">docs/ml-report.md</code>.
            </p>
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <p className="eyebrow">Segurança e LGPD</p>
          </div>
          <div className="card-body space-y-3 text-sm leading-relaxed text-slate-700">
            <p>
              Defesa em profundidade em duas camadas de criptografia (Fernet no Gateway, AES-256-GCM no Core),
              assinatura HMAC nos webhooks de faturamento, JWT RS256 na borda e HS256 internamente. CPF, email e
              telefone são cifrados em repouso e mascarados em todas as respostas e logs.
            </p>
            <p>
              Threat model STRIDE em cinco domínios em
              <code className="ml-1 rounded-sm bg-slate-100 px-1.5 py-0.5 text-xs">docs/threat-model.md</code>.
            </p>
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <p className="eyebrow">Métricas do piloto</p>
          </div>
          <div className="card-body">
            <ul className="space-y-2 text-sm text-slate-700">
              <li>Conversão de risco: percentual de leads de risco que agendaram após abordagem.</li>
              <li>Impacto direto no VIN Share regional em janela de 12 meses.</li>
              <li>Tempo de resposta do consultor entre criação do lead e primeira ação.</li>
              <li>Adoção operacional medida em leads fechados por consultor por dia útil.</li>
            </ul>
          </div>
        </div>
      </section>
    </div>
  );
}
