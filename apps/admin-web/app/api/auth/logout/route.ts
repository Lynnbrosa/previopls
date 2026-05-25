import { NextResponse } from 'next/server';
import { clearSessionCookies } from '@/lib/auth';

export async function POST() {
  clearSessionCookies();
  return NextResponse.json({ ok: true });
}
