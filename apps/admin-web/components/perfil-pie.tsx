'use client';

import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts';

const COLORS: Record<string, string> = {
  FIEL: '#2563eb',
  ABANDONO: '#dc2626',
  ESQUECIDO: '#f59e0b',
  ECONOMICO: '#0d9488',
};

interface DataPoint {
  perfil: string;
  count: number;
}

export function PerfilPie({ data }: { data: DataPoint[] }) {
  if (data.every((d) => d.count === 0)) {
    return <p className="py-12 text-center text-sm text-slate-400">Sem dados de leads ainda.</p>;
  }
  return (
    <div className="h-64 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie data={data} dataKey="count" nameKey="perfil" innerRadius={50} outerRadius={90} paddingAngle={2}>
            {data.map((entry) => (
              <Cell key={entry.perfil} fill={COLORS[entry.perfil] ?? '#94a3b8'} />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{ borderRadius: 6, fontSize: 12, border: '1px solid #e2e8f0' }}
            formatter={(value: number, name: string) => [`${value} leads`, name]}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
