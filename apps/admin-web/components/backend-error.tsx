import { BackendErrorCard } from '@/components/backend-error-card';
import { describeApiError, diagnoseBackend, isTransientError } from '@/lib/api';

/**
 * Card de erro de backend com diagnóstico da cadeia painel → gateway → banco → core.
 * Server component: consulta /health e /version daqui mesmo (a rede em que a leitura falhou)
 * e entrega ao card cliente só dados serializáveis. O card tenta de novo sozinho quando o
 * erro é transitório (backend acordando).
 */
export async function BackendError({ error }: { error: unknown }) {
  const diagnosis = await diagnoseBackend();
  return <BackendErrorCard message={describeApiError(error)} retryable={isTransientError(error)} diagnosis={diagnosis} />;
}
