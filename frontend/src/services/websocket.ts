type MessageCallback = (data: unknown) => void;
type ErrorCallback = (error: Event) => void;

const MAX_RETRIES = 5;
const BASE_DELAY_MS = 1000;

class WebSocketService {
  private ws: WebSocket | null = null;
  private messageCallbacks: MessageCallback[] = [];
  private errorCallbacks: ErrorCallback[] = [];
  private retryCount = 0;
  private clientId: string | null = null;
  private intentionalClose = false;

  connect(clientId: string): void {
    this.clientId = clientId;
    this.intentionalClose = false;
    this.retryCount = 0;
    this.createConnection();
  }

  disconnect(): void {
    this.intentionalClose = true;
    this.clientId = null;
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  send(message: object): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    }
  }

  onMessage(callback: MessageCallback): () => void {
    this.messageCallbacks.push(callback);
    return () => {
      this.messageCallbacks = this.messageCallbacks.filter(
        (cb) => cb !== callback
      );
    };
  }

  onError(callback: ErrorCallback): () => void {
    this.errorCallbacks.push(callback);
    return () => {
      this.errorCallbacks = this.errorCallbacks.filter(
        (cb) => cb !== callback
      );
    };
  }

  // ── Private ─────────────────────────────────────────────────────────────

  private createConnection(): void {
    if (!this.clientId) return;

    const wsBase =
      process.env.REACT_APP_WS_URL || "ws://localhost:8000";
    this.ws = new WebSocket(`${wsBase}/ws/${this.clientId}`);

    this.ws.onopen = () => {
      this.retryCount = 0;
    };

    this.ws.onmessage = (event: MessageEvent) => {
      try {
        const data: unknown = JSON.parse(event.data as string);
        this.messageCallbacks.forEach((cb) => cb(data));
      } catch {
        this.messageCallbacks.forEach((cb) => cb(event.data));
      }
    };

    this.ws.onerror = (event: Event) => {
      this.errorCallbacks.forEach((cb) => cb(event));
    };

    this.ws.onclose = () => {
      if (!this.intentionalClose) {
        this.attemptReconnect();
      }
    };
  }

  private attemptReconnect(): void {
    if (this.retryCount >= MAX_RETRIES || !this.clientId) return;

    const delay = BASE_DELAY_MS * Math.pow(2, this.retryCount);
    this.retryCount += 1;

    setTimeout(() => {
      this.createConnection();
    }, delay);
  }
}

const webSocketService = new WebSocketService();
export default webSocketService;
