'use client';

import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts';
import { PERFIL_HEX, PERFIL_LABEL, PRIORIDADE_HEX, PRIORIDADE_LABEL } from '@/lib/labels';

const DEFAULT_COLORS: Record<string, string> = { ...PERFIL_HEX, ...PRIORIDADE_HEX };
const DEFAULT_LABELS: Record<string, string> = { ...PERFIL_LABEL, ...PRIORIDADE_LABEL };

interface DataPoint {
  perfil: string;
  count: number;
}

export function PerfilPie({
  data,
  colors = DEFAULT_COLORS,
  labels = DEFAULT_LABELS,
}: {
  data: DataPoint[];
  colors?: Record<string, string>;
  labels?: Record<string, string>;
}) {
  if (data.every((d) => d.count === 0)) {
    return <p className="py-12 text-center text-sm text-slate-400">Sem dados de leads ainda.</p>;
  }
  const rows = data.map((d) => ({ ...d, label: labels[d.perfil] ?? d.perfil }));
  return (
    <div className="h-64 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={rows}
            dataKey="count"
            nameKey="label"
            innerRadius={50}
            outerRadius={90}
            paddingAngle={2}
            isAnimationActive={false}
          >
            {rows.map((entry) => (
              <Cell key={entry.perfil} fill={colors[entry.perfil] ?? '#94a3b8'} />
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
