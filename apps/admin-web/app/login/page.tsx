import { redirect } from 'next/navigation';
import { LoginForm } from '@/components/login-form';
import { getSession } from '@/lib/auth';

export default function LoginPage() {
  if (getSession()) {
    redirect('/dashboard');
  }
  return (
    <main className="grid min-h-screen grid-cols-1 lg:grid-cols-2">
      <aside className="hidden flex-col justify-between bg-ford px-12 py-16 text-white lg:flex">
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-[0.3em] text-ford-100">Ford Predict &amp; Care</p>
          <h1 className="mt-6 text-5xl font-bold leading-tight tracking-tight">PrevioPLS</h1>
          <div className="ford-rule mt-6 bg-white" />
          <p className="mt-8 max-w-md text-base leading-relaxed text-ford-50">
            Plataforma preditiva de retenção pós-venda. Classifica cada novo comprador no momento da compra
            e entrega leads acionáveis ao consultor antes da primeira revisão.
          </p>
        </div>
        <div className="space-y-3 text-xs text-ford-100">
          <div className="flex items-center gap-3">
            <span className="h-px w-6 bg-ford-100" />
            <span>Classificação por Machine Learning</span>
          </div>
          <div className="flex items-center gap-3">
            <span className="h-px w-6 bg-ford-100" />
            <span>Scripts comerciais por perfil</span>
          </div>
          <div className="flex items-center gap-3">
            <span className="h-px w-6 bg-ford-100" />
            <span>Conformidade LGPD com trilha de auditoria</span>
          </div>
        </div>
      </aside>

      <section className="flex items-center justify-center bg-white px-6 py-16 lg:px-16">
        <div className="w-full max-w-sm">
          <p className="eyebrow">Entrar no painel</p>
          <h2 className="mt-3 text-3xl font-bold tracking-tight text-slate-900">Bem-vindo de volta</h2>
          <div className="ford-rule mt-4" />
          <div className="mt-10">
            <LoginForm />
          </div>
          <p className="mt-10 text-xs text-slate-400">
            Em desenvolvimento: admin@ford.com / admin123 ou consultor@ford.com / cons123.
          </p>
        </div>
      </section>
    </main>
  );
}
