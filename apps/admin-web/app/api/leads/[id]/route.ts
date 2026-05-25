import { NextResponse } from 'next/server';
import { ApiError, patchLead } from '@/lib/api';

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
    const lead = await patchLead(params.id, {
      status: body.status as never,
      observacao: body.observacao,
    });
    return NextResponse.json(lead);
  } catch (err) {
    if (err instanceof ApiError) {
      return NextResponse.json({ message: 'Falha ao atualizar lead' }, { status: err.status });
    }
    return NextResponse.json({ message: 'Erro inesperado' }, { status: 500 });
  }
}
