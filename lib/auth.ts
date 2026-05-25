import { Secure } from './storage';
import type { RolePapel } from '@/types';

export async function getToken(): Promise<string | null> {
  return Secure.get('jwt');
}

export async function getRole(): Promise<RolePapel | null> {
  const v = await Secure.get('role');
  return v as RolePapel | null;
}

export async function setSession(token: string, role: string): Promise<void> {
  await Secure.set('jwt', token);
  await Secure.set('role', role);
}

export async function clearSession(): Promise<void> {
  await Secure.remove('jwt');
  await Secure.remove('role');
}
