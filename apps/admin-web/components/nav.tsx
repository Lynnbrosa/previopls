'use client';

import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { cn } from '@/lib/utils';

const items = [
  { href: '/dashboard', label: 'Dashboard' },
  { href: '/leads', label: 'Leads' },
  { href: '/about', label: 'Sobre' },
];

export function Nav({ role }: { role: string }) {
  const pathname = usePathname();
  const router = useRouter();

  async function logout() {
    await fetch('/api/auth/logout', { method: 'POST' });
    router.push('/login');
    router.refresh();
  }

  return (
    <header className="sticky top-0 z-40 border-b border-slate-200 bg-white">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-8">
        <div className="flex items-center gap-10">
          <Link href="/dashboard" className="flex items-baseline gap-2">
            <span className="text-xl font-bold tracking-tight text-ford">PrevioPLS</span>
            <span className="text-[10px] font-semibold uppercase tracking-[0.2em] text-slate-400">Admin</span>
          </Link>
          <nav className="hidden items-center gap-8 md:flex">
            {items.map((item) => {
              const active = pathname?.startsWith(item.href);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    'relative py-5 text-sm font-medium transition',
                    active ? 'text-ford' : 'text-slate-600 hover:text-slate-900',
                  )}
                >
                  {item.label}
                  {active && <span className="absolute inset-x-0 -bottom-px h-0.5 bg-ford" />}
                </Link>
              );
            })}
          </nav>
        </div>
        <div className="flex items-center gap-4">
          <span className="hidden text-[10px] font-semibold uppercase tracking-[0.2em] text-slate-500 md:inline">
            {role}
          </span>
          <button onClick={logout} className="btn-ghost">
            Sair
          </button>
        </div>
      </div>
    </header>
  );
}
