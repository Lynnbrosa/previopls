import { redirect } from 'next/navigation';
import { Nav } from '@/components/nav';
import { getSession } from '@/lib/auth';

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const session = getSession();
  if (!session) {
    redirect('/login');
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <Nav role={session.role} />
      <main className="mx-auto max-w-7xl px-8 py-10">{children}</main>
      <footer className="border-t border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-8 py-6 text-xs text-slate-500">
          <span>PrevioPLS · Ford Predict &amp; Care · Challenge FIAP 2026</span>
          <span>v1.0.0</span>
        </div>
      </footer>
    </div>
  );
}
