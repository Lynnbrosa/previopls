export function BackendError({ message }: { message: string }) {
  return (
    <div className="card border-l-4 border-l-red-600">
      <div className="card-header">
        <p className="eyebrow">Backend indisponível</p>
      </div>
      <div className="card-body space-y-2 text-sm text-slate-700">
        <p>{message}</p>
        <p className="text-xs text-slate-500">
          O painel lê os dados pelo servidor (INTERNAL_GATEWAY_URL). Confira o <code>/health</code> do Gateway e do Core e
          os logs do container <code>admin-web</code>.
        </p>
      </div>
    </div>
  );
}
