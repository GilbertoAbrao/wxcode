/**
 * WebSocket client para comunicação com o chat backend.
 */

import type { StreamMessage, ChatContext, ClientMessage } from "@/types/chat";

interface ChatWebSocketOptions {
  onMessage: (message: StreamMessage) => void;
  onConnect: () => void;
  onDisconnect: () => void;
  onError: () => void;
}

export class ChatWebSocket {
  private ws: WebSocket | null = null;
  private projectId: string;
  private options: ChatWebSocketOptions;
  private _isConnected = false;

  constructor(projectId: string, options: ChatWebSocketOptions) {
    this.projectId = projectId;
    this.options = options;
  }

  get isConnected(): boolean {
    return this._isConnected;
  }

  async connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
        const host = window.location.host;
        const url = `${protocol}//${host}/api/chat/${this.projectId}/ws`;

        this.ws = new WebSocket(url);

        this.ws.onopen = () => {
          this._isConnected = true;
          this.options.onConnect();
          resolve();
        };

        this.ws.onmessage = (event: MessageEvent) => {
          try {
            const message: StreamMessage = JSON.parse(event.data);
            this.options.onMessage(message);
          } catch (err) {
            console.error("Failed to parse WebSocket message:", err);
          }
        };

        this.ws.onclose = () => {
          this._isConnected = false;
          this.options.onDisconnect();
        };

        this.ws.onerror = () => {
          this._isConnected = false;
          this.options.onError();
          reject(new Error("WebSocket connection failed"));
        };
      } catch (err) {
        reject(err);
      }
    });
  }

  disconnect(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
      this._isConnected = false;
    }
  }

  send(content: string, context: ChatContext): void {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      console.error("WebSocket is not connected");
      return;
    }

    const message: ClientMessage = {
      type: "message",
      content,
      context,
    };

    this.ws.send(JSON.stringify(message));
  }
}
