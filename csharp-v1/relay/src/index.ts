export interface Env { ROOMS: DurableObjectNamespace }

type Packet = { type?: string; room?: string; name?: string; role?: string; data?: string; from?: string; members?: string[]; ticks?: number };

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);
    if (url.pathname === "/health") return new Response("Riu relay online");
    if (url.pathname !== "/ws" || request.headers.get("Upgrade")?.toLowerCase() !== "websocket") return new Response("WebSocket required", { status: 426 });
    const room = (url.searchParams.get("room") || "LOBBY").toUpperCase();
    const id = env.ROOMS.idFromName(room);
    return env.ROOMS.get(id).fetch(request);
  }
};

export class Room {
  private state: DurableObjectState;
  private sockets = new Map<WebSocket, { name: string; role: string }>();
  constructor(state: DurableObjectState) { this.state = state; }

  async fetch(request: Request): Promise<Response> {
    if (request.headers.get("Upgrade")?.toLowerCase() !== "websocket") return new Response("WebSocket required", { status: 426 });
    const pair = new WebSocketPair();
    const client = pair[0], server = pair[1];
    server.accept();
    this.sockets.set(server, { name: "Player", role: "MEMBER" });

    server.addEventListener("message", e => this.onMessage(server, String(e.data)));
    server.addEventListener("close", () => this.onClose(server));
    server.addEventListener("error", () => this.onClose(server));
    return new Response(null, { status: 101, webSocket: client });
  }

  private send(ws: WebSocket, packet: Packet) { try { ws.send(JSON.stringify(packet)); } catch {} }
  private broadcast(packet: Packet) { const text = JSON.stringify(packet); for (const ws of this.sockets.keys()) try { ws.send(text); } catch {} }
  private members() { return [...this.sockets.values()].map(x => x.name).filter(Boolean); }
  private pushMembers() { this.broadcast({ type: "members", members: this.members() }); }

  private onMessage(ws: WebSocket, raw: string) {
    let p: Packet;
    try { p = JSON.parse(raw); } catch { return; }
    const meta = this.sockets.get(ws); if (!meta) return;

    if (p.type === "hello") {
      meta.name = (p.name || "Player").slice(0, 24);
      meta.role = p.role === "OWNER" ? "OWNER" : "MEMBER";
      this.broadcast({ type: "joined", name: meta.name });
      this.pushMembers();
      return;
    }
    if (p.type === "ping") { this.send(ws, { type: "pong", ticks: p.ticks || 0 }); return; }
    if (p.type === "action") {
      this.broadcast({ type: "action", data: p.data || "", from: meta.name });
      return;
    }
  }

  private onClose(ws: WebSocket) {
    const meta = this.sockets.get(ws);
    this.sockets.delete(ws);
    if (meta) this.broadcast({ type: "left", name: meta.name });
    this.pushMembers();
  }
}
