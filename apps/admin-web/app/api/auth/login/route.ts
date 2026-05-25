import { NextResponse } from 'next/server';
import { setSessionCookies } from '@/lib/auth';
import { login } from '@/lib/api';

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
  } catch (err: any) {
    const status = err?.status ?? 401;
    return NextResponse.json({ message: 'Credenciais inválidas' }, { status });
  }
}
