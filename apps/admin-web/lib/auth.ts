import { cookies } from 'next/headers';

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

export function setSessionCookies(token: string, role: string, maxAgeSeconds: number) {
  const store = cookies();
  store.set(COOKIE_NAME, token, {
    httpOnly: true,
    secure: true,
    sameSite: 'lax',
    path: '/',
    maxAge: maxAgeSeconds,
  });
  store.set(COOKIE_ROLE, role, {
    httpOnly: false,
    secure: true,
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
