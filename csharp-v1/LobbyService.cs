using System.Net.WebSockets;
using System.Text;
using System.Text.Json;

namespace RiuClicker;

public sealed class LobbyService : IAsyncDisposable
{
    private sealed class Packet
    {
        public string Type { get; set; } = "";
        public string Room { get; set; } = "";
        public string Name { get; set; } = "";
        public string Role { get; set; } = "";
        public string Data { get; set; } = "";
        public string From { get; set; } = "";
        public List<string>? Members { get; set; }
        public long Ticks { get; set; }
    }

    private readonly JsonSerializerOptions _json = new(JsonSerializerDefaults.Web);
    private readonly SemaphoreSlim _sendLock = new(1,1);
    private ClientWebSocket? _ws;
    private CancellationTokenSource? _cts;
    private Task? _readLoop;
    private Task? _pingLoop;
    private string _displayName = "Player";
    private string _room = "";
    private string _role = "OFFLINE";
    private Uri? _relayUri;

    public event Action<IReadOnlyList<string>>? MembersChanged;
    public event Action<string>? StatusChanged;
    public event Action<string>? RoleChanged;
    public event Action<string>? Log;
    public event Action<long>? PingChanged;
    public event Action<string,string>? ActionReceived;

    public string Role => _role;
    public string LobbyCode => _room.Length == 0 ? "" : $"RIU-{_room}";

    public async Task<string> HostAsync(string displayName, string relayUrl)
    {
        await StopAsync();
        _displayName = CleanName(displayName);
        _room = RandomRoom();
        _role = "OWNER";
        await ConnectAsync(relayUrl, _room, _displayName, _role);
        return LobbyCode;
    }

    public async Task JoinAsync(string code, string displayName, string relayUrl)
    {
        await StopAsync();
        _displayName = CleanName(displayName);
        _room = NormalizeRoom(code);
        if (_room.Length != 6) throw new InvalidOperationException("Invalid lobby code.");
        _role = "MEMBER";
        await ConnectAsync(relayUrl, _room, _displayName, _role);
    }

    private async Task ConnectAsync(string relayUrl, string room, string name, string role)
    {
        if (!Uri.TryCreate(relayUrl?.Trim(), UriKind.Absolute, out var uri) || (uri.Scheme != "ws" && uri.Scheme != "wss"))
            throw new InvalidOperationException("Relay URL is not configured. Use a wss:// Cloudflare Worker address.");

        _relayUri = uri;
        _cts = new CancellationTokenSource();
        _ws = new ClientWebSocket();
        _ws.Options.KeepAliveInterval = TimeSpan.FromSeconds(10);
        using var timeout = CancellationTokenSource.CreateLinkedTokenSource(_cts.Token);
        timeout.CancelAfter(TimeSpan.FromSeconds(8));
        try { await _ws.ConnectAsync(uri, timeout.Token); }
        catch (Exception ex)
        {
            await StopAsync();
            throw new InvalidOperationException("Could not connect to relay server.", ex);
        }

        await SendAsync(new Packet { Type="hello", Room=room, Name=name, Role=role }, _cts.Token);
        RoleChanged?.Invoke(role);
        StatusChanged?.Invoke("Relay connected");
        Log?.Invoke($"Connected to relay · {LobbyCode}");
        _readLoop = Task.Run(() => ReadLoopAsync(_cts.Token));
        _pingLoop = Task.Run(() => PingLoopAsync(_cts.Token));
    }

    public async Task SendActionAsync(string action)
    {
        action = (action ?? "").Trim();
        if (action.Length == 0) return;
        if (_ws?.State != WebSocketState.Open) throw new InvalidOperationException("Not connected to relay.");
        await SendAsync(new Packet { Type="action", Room=_room, Data=action, From=_displayName }, _cts?.Token ?? CancellationToken.None);
    }

    private async Task ReadLoopAsync(CancellationToken ct)
    {
        byte[] buffer = new byte[16 * 1024];
        try
        {
            while (!ct.IsCancellationRequested && _ws?.State == WebSocketState.Open)
            {
                using var ms = new MemoryStream();
                WebSocketReceiveResult result;
                do
                {
                    result = await _ws.ReceiveAsync(buffer, ct);
                    if (result.MessageType == WebSocketMessageType.Close) break;
                    ms.Write(buffer, 0, result.Count);
                } while (!result.EndOfMessage);
                if (result.MessageType == WebSocketMessageType.Close) break;

                var packet = JsonSerializer.Deserialize<Packet>(ms.ToArray(), _json);
                if (packet is null) continue;
                switch (packet.Type)
                {
                    case "members": MembersChanged?.Invoke(packet.Members ?? new()); break;
                    case "joined": Log?.Invoke($"{packet.Name} joined"); break;
                    case "left": Log?.Invoke($"{packet.Name} left"); break;
                    case "pong": PingChanged?.Invoke(Math.Max(0, DateTimeOffset.UtcNow.ToUnixTimeMilliseconds() - packet.Ticks)); break;
                    case "action": ActionReceived?.Invoke(packet.From.Length == 0 ? "Player" : packet.From, packet.Data); break;
                    case "error": Log?.Invoke(packet.Data); break;
                }
            }
        }
        catch (OperationCanceledException) { return; }
        catch (Exception ex) { Log?.Invoke("Relay error: " + ex.Message); }
        if (!ct.IsCancellationRequested)
        {
            StatusChanged?.Invoke("Relay disconnected");
            await StopAsync();
        }
    }

    private async Task PingLoopAsync(CancellationToken ct)
    {
        while (!ct.IsCancellationRequested)
        {
            try
            {
                await SendAsync(new Packet { Type="ping", Room=_room, Ticks=DateTimeOffset.UtcNow.ToUnixTimeMilliseconds() }, ct);
                await Task.Delay(1000, ct);
            }
            catch (OperationCanceledException) { break; }
            catch { break; }
        }
    }

    private async Task SendAsync(Packet packet, CancellationToken ct)
    {
        if (_ws?.State != WebSocketState.Open) throw new InvalidOperationException("Relay is offline.");
        byte[] bytes = JsonSerializer.SerializeToUtf8Bytes(packet, _json);
        await _sendLock.WaitAsync(ct);
        try { await _ws.SendAsync(bytes, WebSocketMessageType.Text, true, ct); }
        finally { _sendLock.Release(); }
    }

    public async Task StopAsync()
    {
        var cts = Interlocked.Exchange(ref _cts, null);
        try { cts?.Cancel(); } catch { }
        if (_ws is not null)
        {
            try
            {
                if (_ws.State == WebSocketState.Open)
                    await _ws.CloseAsync(WebSocketCloseStatus.NormalClosure, "bye", CancellationToken.None);
            }
            catch { }
            _ws.Dispose();
            _ws = null;
        }
        _room = "";
        PingChanged?.Invoke(-1);
        MembersChanged?.Invoke(Array.Empty<string>());
        if (_role != "OFFLINE")
        {
            _role = "OFFLINE";
            RoleChanged?.Invoke(_role);
            StatusChanged?.Invoke("Offline");
        }
        cts?.Dispose();
    }

    private static string CleanName(string? name)
    {
        string value = string.IsNullOrWhiteSpace(name) ? "Player" : name.Trim();
        value = new string(value.Where(ch => !char.IsControl(ch)).ToArray());
        return value.Length > 24 ? value[..24] : value;
    }

    private static string RandomRoom()
    {
        const string chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789";
        Span<byte> bytes = stackalloc byte[6];
        System.Security.Cryptography.RandomNumberGenerator.Fill(bytes);
        var sb = new StringBuilder(6);
        foreach (byte b in bytes) sb.Append(chars[b % chars.Length]);
        return sb.ToString();
    }

    private static string NormalizeRoom(string? code)
    {
        string s = (code ?? "").Trim().ToUpperInvariant().Replace("RIU-", "").Replace(" ", "");
        return new string(s.Where(char.IsLetterOrDigit).ToArray());
    }

    public async ValueTask DisposeAsync()
    {
        await StopAsync();
        _sendLock.Dispose();
    }
}
