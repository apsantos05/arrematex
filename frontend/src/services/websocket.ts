/**
 * WebSocket service — conecta ao canal do leilão ou do telão.
 * Reconecta automaticamente com backoff exponencial.
 */

type MessageHandler = (data: Record<string, unknown>) => void;
type StatusHandler = (status: "connecting" | "connected" | "error") => void;

class ArrematexWebSocket {
  private ws: WebSocket | null = null;
  private handlers: MessageHandler[] = [];
  private url = "";
  private reconnectDelay = 1000;
  private maxDelay = 30000;
  private shouldReconnect = true;
  private pingInterval: ReturnType<typeof setInterval> | null = null;
  onStatusChange: StatusHandler | null = null;

  connect(channel: "leilao" | "telao", eventoId: string, token?: string) {
    const base = import.meta.env.VITE_WS_URL || `ws://${window.location.host}`;
    const tokenParam = token ? `?token=${token}` : "";
    this.url = `${base}/ws/${channel}/${eventoId}/${tokenParam}`;
    this.shouldReconnect = true;
    this._connect();
  }

  private _connect() {
    this.onStatusChange?.("connecting");
    this.ws = new WebSocket(this.url);

    this.ws.onopen = () => {
      console.info("[WS] Conectado:", this.url);
      this.reconnectDelay = 1000;
      this.onStatusChange?.("connected");
      // Keep-alive ping a cada 25s
      this.pingInterval = setInterval(() => {
        this.send({ action: "ping" });
      }, 25000);
    };

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        this.handlers.forEach((h) => h(data));
      } catch {
        /* ignore */
      }
    };

    this.ws.onclose = () => {
      if (this.pingInterval) clearInterval(this.pingInterval);
      this.onStatusChange?.("error");
      if (this.shouldReconnect) {
        console.warn(`[WS] Desconectado. Reconectando em ${this.reconnectDelay}ms`);
        setTimeout(() => this._connect(), this.reconnectDelay);
        this.reconnectDelay = Math.min(this.reconnectDelay * 2, this.maxDelay);
      }
    };

    this.ws.onerror = (e) => {
      console.error("[WS] Erro:", e);
      this.onStatusChange?.("error");
      this.ws?.close();
    };
  }

  send(data: Record<string, unknown>) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
      return true;
    }
    return false;
  }

  on(handler: MessageHandler) {
    this.handlers.push(handler);
    return () => {
      this.handlers = this.handlers.filter((h) => h !== handler);
    };
  }

  disconnect() {
    this.shouldReconnect = false;
    if (this.pingInterval) clearInterval(this.pingInterval);
    this.ws?.close();
  }
}

export const leilaoWS = new ArrematexWebSocket();
export const telaoWS = new ArrematexWebSocket();
