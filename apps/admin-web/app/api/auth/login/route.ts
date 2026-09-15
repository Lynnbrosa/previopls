import { NextResponse } from 'next/server';
import { setSessionCookies } from '@/lib/auth';
import { ApiError, login } from '@/lib/api';

export async function POST(request: Request) {
  let body: { email?: string; senha?: string };
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ message: 'Payload inválido' }, { status: 400 });
  }
  if (!body.email || !body.senha) {
    return NextResponse.json({ message: 'Email e senha obrigatórios' }, { status: 422 });
  }
  try {
    const response = await login({ email: body.email, senha: body.senha });
    setSessionCookies(response.accessToken, response.role, response.expiresIn);
    return NextResponse.json({ role: response.role });
  } catch (err) {
    // Mensagens distintas para o usuário: credencial errada, lockout/rate limit e backend fora.
    if (err instanceof ApiError) {
      if (err.status === 429) {
        return NextResponse.json({ message: 'Muitas tentativas. Aguarde um minuto e tente novamente.' }, { status: 429 });
      }
      if (err.status === 401 || err.status === 403) {
        return NextResponse.json({ message: 'Credenciais inválidas ou conta bloqueada temporariamente.' }, { status: 401 });
      }
      if (err.status >= 500) {
        return NextResponse.json({ message: 'Backend indisponível no momento.' }, { status: 503 });
      }
      return NextResponse.json({ message: 'Falha ao autenticar.' }, { status: err.status });
    }
    return NextResponse.json({ message: 'Não foi possível conectar ao backend.' }, { status: 503 });
  }
}
