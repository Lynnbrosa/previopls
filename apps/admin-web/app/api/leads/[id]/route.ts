import { NextResponse } from 'next/server';
import { ApiError, describeApiError, forwardingHeaders, patchLead } from '@/lib/api';

export const maxDuration = 60;
export const dynamic = 'force-dynamic';

export async function PATCH(request: Request, { params }: { params: { id: string } }) {
  let body: { status?: string; observacao?: string };
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ message: 'Payload inválido' }, { status: 400 });
  }
  if (!body.status) {
    return NextResponse.json({ message: 'Status obrigatório' }, { status: 422 });
  }
  try {
    const lead = await patchLead(
      params.id,
      { status: body.status as never, observacao: body.observacao },
      forwardingHeaders(request),
    );
    return NextResponse.json(lead);
  } catch (err) {
    if (err instanceof ApiError) {
      const message =
        err.status === 401 ? 'Sessão expirada. Entre novamente.'
        : err.status === 403 ? 'Seu papel não pode alterar leads.'
        : err.status === 404 ? 'Lead não encontrado.'
        : err.status === 429 ? 'Muitas requisições. Aguarde um instante.'
        : err.status >= 500 ? describeApiError(err)
        : 'Falha ao atualizar lead.';
      return NextResponse.json({ message }, { status: err.status });
    }
    return NextResponse.json({ message: 'Não foi possível conectar ao backend.' }, { status: 503 });
  }
}
