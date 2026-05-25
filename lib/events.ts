type Listener = () => void;

class TinyEmitter {
  private listeners: Map<string, Set<Listener>> = new Map();

  on(event: string, listener: Listener): () => void {
    if (!this.listeners.has(event)) this.listeners.set(event, new Set());
    this.listeners.get(event)!.add(listener);
    return () => this.listeners.get(event)?.delete(listener);
  }

  emit(event: string): void {
    this.listeners.get(event)?.forEach((l) => l());
  }
}

export const events = new TinyEmitter();

export const AUTH_EXPIRED = 'auth:expired';
