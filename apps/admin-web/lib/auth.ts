import { cookies, headers } from 'next/headers';

const COOKIE_NAME = 'previopls_jwt';
const COOKIE_ROLE = 'previopls_role';

export interface SessionData {
  token: string;
  role: string;
}

export function getSession(): SessionData | null {
  const store = cookies();
  const token = store.get(COOKIE_NAME)?.value;
  const role = store.get(COOKIE_ROLE)?.value;
  if (!token || !role) return null;
  return { token, role };
}

/**
 * Cookie Secure só quando a requisição chegou por HTTPS. nginx e Vercel enviam
 * X-Forwarded-Proto; o próprio servidor do Next.js preenche o header quando não há proxy.
 * Com Secure fixo, um `npm run dev` aberto por http://<ip-da-lan>:3000 fazia o navegador
 * descartar o cookie: o login respondia 200 e a página voltava para /login.
 */
function servedOverHttps(): boolean {
  const h = headers();
  const proto = h.get('x-forwarded-proto');
  if (proto) return proto.split(',')[0].trim() === 'https';
  // Sem header (caso raro): só localhost, onde os navegadores aceitam Secure em http.
  const host = h.get('host') ?? '';
  return host.startsWith('localhost') || host.startsWith('127.0.0.1');
}

export function setSessionCookies(token: string, role: string, maxAgeSeconds: number) {
  const store = cookies();
  const secure = servedOverHttps();
  store.set(COOKIE_NAME, token, {
    httpOnly: true,
    secure,
    sameSite: 'lax',
    path: '/',
    maxAge: maxAgeSeconds,
  });
  store.set(COOKIE_ROLE, role, {
    httpOnly: false,
    secure,
    sameSite: 'lax',
    path: '/',
    maxAge: maxAgeSeconds,
  });
}

export function clearSessionCookies() {
  const store = cookies();
  store.delete(COOKIE_NAME);
  store.delete(COOKIE_ROLE);
}

export const COOKIE_NAMES = { jwt: COOKIE_NAME, role: COOKIE_ROLE };
