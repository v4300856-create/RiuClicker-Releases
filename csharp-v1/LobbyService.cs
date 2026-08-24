using System.Collections.Concurrent;
using System.IO;
using System.Net;
using System.Net.Http;
using System.Net.NetworkInformation;
using System.Net.Sockets;
using System.Text;
using System.Text.Json;

namespace RiuClicker;

public sealed class LobbyService : IAsyncDisposable
{
    private sealed class Packet
    {
        public string Type { get; set; } = "";
        public string? Name { get; set; }
        public List<string>? Members { get; set; }
        public long Ticks { get; set; }
        public string? Data { get; set; }
        public string? From { get; set; }
    }

    private sealed class Peer : IAsyncDisposable
    {
        public Guid Id { get; } = Guid.NewGuid();
        public TcpClient Client { get; }
        public StreamReader Reader { get; }
        public StreamWriter Writer { get; }
        public SemaphoreSlim SendLock { get; } = new(1, 1);
        public string Name { get; set; } = "Player";

        public Peer(TcpClient client)
        {
            Client = client;
            var stream = client.GetStream();
            Reader = new StreamReader(stream, new UTF8Encoding(false), false, 4096, leaveOpen: true);
            Writer = new StreamWriter(stream, new UTF8Encoding(false), 4096, leaveOpen: true)
            {
                AutoFlush = true,
                NewLine = "\n"
            };
        }

        public async ValueTask DisposeAsync()
        {
            try { Writer.Dispose(); } catch { }
            try { Reader.Dispose(); } catch { }
            try { Client.Close(); } catch { }
            SendLock.Dispose();
            await ValueTask.CompletedTask;
        }
    }

    private readonly ConcurrentDictionary<Guid, Peer> _peers = new();
    private readonly JsonSerializerOptions _json = new(JsonSerializerDefaults.Web);
    private readonly SemaphoreSlim _clientSendLock = new(1, 1);
    private CancellationTokenSource? _cts;
    private TcpListener? _listener;
    private TcpClient? _client;
    private StreamReader? _clientReader;
    private StreamWriter? _clientWriter;
    private Task? _acceptLoop;
    private Task? _clientReadLoop;
    private Task? _pingLoop;
    private string _displayName = "Player";
    private string _role = "OFFLINE";
    private long _lastPingMs = -1;

    public event Action<IReadOnlyList<string>>? MembersChanged;
    public event Action<string>? StatusChanged;
    public event Action<string>? RoleChanged;
    public event Action<string>? Log;
    public event Action<long>? PingChanged;
    public event Action<string, string>? ActionReceived;

    public string Role => _role;
    public string LobbyCode { get; private set; } = "";

    public async Task<string> HostAsync(string displayName, int port)
    {
        await StopAsync();
        _displayName = CleanName(displayName);
        port = Math.Clamp(port, 1024, 65535);
        _cts = new CancellationTokenSource();
        _role = "OWNER";
        RoleChanged?.Invoke(_role);

        _listener = new TcpListener(IPAddress.Any, port);
        _listener.Server.SetSocketOption(SocketOptionLevel.Socket, SocketOptionName.ReuseAddress, true);
        _listener.Start(32);

        string localIp = GetLocalIpv4() ?? "127.0.0.1";
        _ = Task.Run(() => TryOpenUpnpPort(port, localIp));
        string publicIp = await GetPublicIpAsync(_cts.Token) ?? localIp;
        LobbyCode = BuildCode(publicIp, localIp, port);

        MembersChanged?.Invoke(new[] { _displayName });
        StatusChanged?.Invoke("Lobby online");
        Log?.Invoke($"Lobby created on port {port}");
        _acceptLoop = Task.Run(() => AcceptLoopAsync(_cts.Token));
        return LobbyCode;
    }

    public async Task JoinAsync(string code, string displayName)
    {
        await StopAsync();
        _displayName = CleanName(displayName);
        _cts = new CancellationTokenSource();

        var endpoints = ParseCode(code);
        if (endpoints.Count == 0)
            throw new InvalidOperationException("Invalid lobby code.");

        string? myPublic = await GetPublicIpAsync(_cts.Token);
        if (myPublic is not null && endpoints.Count > 1 && string.Equals(myPublic, endpoints[0].Host, StringComparison.OrdinalIgnoreCase))
            endpoints.Reverse();

        Exception? last = null;
        foreach (var ep in endpoints.DistinctBy(x => $"{x.Host}:{x.Port}"))
        {
            var candidate = new TcpClient(AddressFamily.InterNetwork);
            try
            {
                using var timeout = CancellationTokenSource.CreateLinkedTokenSource(_cts.Token);
                timeout.CancelAfter(TimeSpan.FromSeconds(2.5));
                await candidate.ConnectAsync(ep.Host, ep.Port, timeout.Token);
                ConfigureSocket(candidate.Client);
                _client = candidate;
                break;
            }
            catch (Exception ex)
            {
                last = ex;
                candidate.Dispose();
            }
        }

        if (_client is null)
        {
            await StopAsync();
            throw new InvalidOperationException("Could not connect to lobby. If you are on different networks, the owner router must allow the lobby port (UPnP or port forwarding).", last);
        }

        var stream = _client.GetStream();
        _clientReader = new StreamReader(stream, new UTF8Encoding(false), false, 4096, leaveOpen: true);
        _clientWriter = new StreamWriter(stream, new UTF8Encoding(false), 4096, leaveOpen: true)
        {
            AutoFlush = true,
            NewLine = "\n"
        };

        await SendClientAsync(new Packet { Type = "hello", Name = _displayName }, _cts.Token);
        _role = "MEMBER";
        RoleChanged?.Invoke(_role);
        StatusChanged?.Invoke("Connected");
        Log?.Invoke("Connected to lobby");
        _clientReadLoop = Task.Run(() => ClientReadLoopAsync(_cts.Token));
        _pingLoop = Task.Run(() => ClientPingLoopAsync(_cts.Token));
    }

    public async Task SendActionAsync(string action)
    {
        action = (action ?? "").Trim();
        if (action.Length == 0) return;
        var ct = _cts?.Token ?? CancellationToken.None;

        if (_role == "OWNER")
        {
            ActionReceived?.Invoke(_displayName, action);
            await BroadcastAsync(new Packet { Type = "action", Data = action, From = _displayName }, null, ct);
        }
        else if (_role == "MEMBER")
        {
            await SendClientAsync(new Packet { Type = "action", Data = action, From = _displayName }, ct);
        }
    }

    public async Task StopAsync()
    {
        var cts = Interlocked.Exchange(ref _cts, null);
        try { cts?.Cancel(); } catch { }

        try { _listener?.Stop(); } catch { }
        _listener = null;

        foreach (var peer in _peers.Values)
        {
            _peers.TryRemove(peer.Id, out _);
            try { await peer.DisposeAsync(); } catch { }
        }

        try { _clientWriter?.Dispose(); } catch { }
        try { _clientReader?.Dispose(); } catch { }
        try { _client?.Close(); } catch { }
        _clientWriter = null;
        _clientReader = null;
        _client = null;

        LobbyCode = "";
        _lastPingMs = -1;
        PingChanged?.Invoke(-1);
        if (_role != "OFFLINE")
        {
            _role = "OFFLINE";
            RoleChanged?.Invoke(_role);
            MembersChanged?.Invoke(Array.Empty<string>());
            StatusChanged?.Invoke("Offline");
        }
        cts?.Dispose();
    }

    private async Task AcceptLoopAsync(CancellationToken ct)
    {
        while (!ct.IsCancellationRequested && _listener is not null)
        {
            TcpClient tcp;
            try { tcp = await _listener.AcceptTcpClientAsync(ct); }
            catch (OperationCanceledException) { break; }
            catch (ObjectDisposedException) { break; }
            catch (Exception ex) { Log?.Invoke($"Accept error: {ex.Message}"); continue; }

            ConfigureSocket(tcp.Client);
            _ = Task.Run(() => HandlePeerAsync(tcp, ct), ct);
        }
    }

    private async Task HandlePeerAsync(TcpClient tcp, CancellationToken ct)
    {
        var peer = new Peer(tcp);
        bool joined = false;
        try
        {
            string? line = await peer.Reader.ReadLineAsync(ct);
            if (line is null) return;
            var hello = JsonSerializer.Deserialize<Packet>(line, _json);
            if (hello?.Type != "hello") return;

            peer.Name = CleanName(hello.Name);
            _peers[peer.Id] = peer;
            joined = true;
            Log?.Invoke($"{peer.Name} joined");
            await BroadcastMembersAsync(ct);

            while (!ct.IsCancellationRequested)
            {
                line = await peer.Reader.ReadLineAsync(ct);
                if (line is null) break;
                var packet = JsonSerializer.Deserialize<Packet>(line, _json);
                if (packet is null) continue;

                switch (packet.Type)
                {
                    case "ping":
                        await SendPeerAsync(peer, new Packet { Type = "pong", Ticks = packet.Ticks }, ct);
                        break;
                    case "action":
                        string action = packet.Data ?? "";
                        ActionReceived?.Invoke(peer.Name, action);
                        await BroadcastAsync(new Packet { Type = "action", Data = action, From = peer.Name }, null, ct);
                        break;
                }
            }
        }
        catch (OperationCanceledException) { }
        catch (IOException) { }
        catch (Exception ex) { Log?.Invoke($"Peer error: {ex.Message}"); }
        finally
        {
            if (joined)
            {
                _peers.TryRemove(peer.Id, out _);
                Log?.Invoke($"{peer.Name} left");
                try { await BroadcastMembersAsync(ct); } catch { }
            }
            await peer.DisposeAsync();
        }
    }

    private async Task ClientReadLoopAsync(CancellationToken ct)
    {
        try
        {
            while (!ct.IsCancellationRequested && _clientReader is not null)
            {
                string? line = await _clientReader.ReadLineAsync(ct);
                if (line is null) break;
                var packet = JsonSerializer.Deserialize<Packet>(line, _json);
                if (packet is null) continue;

                switch (packet.Type)
                {
                    case "members":
                        MembersChanged?.Invoke(packet.Members ?? new List<string>());
                        break;
                    case "pong":
                        long now = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds();
                        _lastPingMs = Math.Max(0, now - packet.Ticks);
                        PingChanged?.Invoke(_lastPingMs);
                        break;
                    case "action":
                        ActionReceived?.Invoke(packet.From ?? "Player", packet.Data ?? "");
                        break;
                }
            }
        }
        catch (OperationCanceledException) { return; }
        catch (IOException) { }
        catch (Exception ex) { Log?.Invoke($"Network error: {ex.Message}"); }

        if (!ct.IsCancellationRequested)
        {
            Log?.Invoke("Connection lost");
            await StopAsync();
        }
    }

    private async Task ClientPingLoopAsync(CancellationToken ct)
    {
        while (!ct.IsCancellationRequested)
        {
            try
            {
                await SendClientAsync(new Packet
                {
                    Type = "ping",
                    Ticks = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds()
                }, ct);
                await Task.Delay(500, ct);
            }
            catch (OperationCanceledException) { break; }
            catch
            {
                if (!ct.IsCancellationRequested) await StopAsync();
                break;
            }
        }
    }

    private async Task BroadcastMembersAsync(CancellationToken ct)
    {
        var members = new List<string> { _displayName };
        members.AddRange(_peers.Values.Select(p => p.Name));
        members = members.Distinct(StringComparer.OrdinalIgnoreCase).ToList();
        MembersChanged?.Invoke(members);
        await BroadcastAsync(new Packet { Type = "members", Members = members }, null, ct);
    }

    private async Task BroadcastAsync(Packet packet, Guid? exceptPeerId, CancellationToken ct)
    {
        var tasks = _peers.Values
            .Where(p => p.Id != exceptPeerId)
            .Select(p => SendPeerSafeAsync(p, packet, ct));
        await Task.WhenAll(tasks);
    }

    private async Task SendPeerSafeAsync(Peer peer, Packet packet, CancellationToken ct)
    {
        try { await SendPeerAsync(peer, packet, ct); }
        catch
        {
            _peers.TryRemove(peer.Id, out _);
            try { await peer.DisposeAsync(); } catch { }
        }
    }

    private async Task SendPeerAsync(Peer peer, Packet packet, CancellationToken ct)
    {
        string line = JsonSerializer.Serialize(packet, _json);
        await peer.SendLock.WaitAsync(ct);
        try { await peer.Writer.WriteLineAsync(line.AsMemory(), ct); }
        finally { peer.SendLock.Release(); }
    }

    private async Task SendClientAsync(Packet packet, CancellationToken ct)
    {
        if (_clientWriter is null) throw new InvalidOperationException("Not connected.");
        string line = JsonSerializer.Serialize(packet, _json);
        await _clientSendLock.WaitAsync(ct);
        try { await _clientWriter.WriteLineAsync(line.AsMemory(), ct); }
        finally { _clientSendLock.Release(); }
    }

    private static void ConfigureSocket(Socket socket)
    {
        socket.NoDelay = true;
        socket.SetSocketOption(SocketOptionLevel.Socket, SocketOptionName.KeepAlive, true);
        socket.ReceiveBufferSize = 16 * 1024;
        socket.SendBufferSize = 16 * 1024;
        try
        {
            byte[] values = new byte[12];
            BitConverter.GetBytes((uint)1).CopyTo(values, 0);
            BitConverter.GetBytes((uint)3000).CopyTo(values, 4);
            BitConverter.GetBytes((uint)1000).CopyTo(values, 8);
            socket.IOControl(IOControlCode.KeepAliveValues, values, null);
        }
        catch { }
    }

    private static string CleanName(string? name)
    {
        string value = string.IsNullOrWhiteSpace(name) ? "Player" : name.Trim();
        value = new string(value.Where(ch => !char.IsControl(ch)).ToArray());
        return value.Length > 24 ? value[..24] : value;
    }

    private static string BuildCode(string publicIp, string localIp, int port)
    {
        string payload = $"{publicIp}|{localIp}|{port}";
        return "RIU1." + Convert.ToBase64String(Encoding.UTF8.GetBytes(payload))
            .TrimEnd('=').Replace('+', '-').Replace('/', '_');
    }

    private sealed record EndpointInfo(string Host, int Port);

    private static List<EndpointInfo> ParseCode(string code)
    {
        code = (code ?? "").Trim();
        var result = new List<EndpointInfo>();
        try
        {
            if (code.StartsWith("RIU1.", StringComparison.OrdinalIgnoreCase))
            {
                string b64 = code[5..].Replace('-', '+').Replace('_', '/');
                b64 = b64.PadRight(b64.Length + ((4 - b64.Length % 4) % 4), '=');
                string payload = Encoding.UTF8.GetString(Convert.FromBase64String(b64));
                string[] parts = payload.Split('|');
                if (parts.Length == 3 && int.TryParse(parts[2], out int port))
                {
                    result.Add(new EndpointInfo(parts[0], port));
                    if (!string.Equals(parts[1], parts[0], StringComparison.OrdinalIgnoreCase))
                        result.Add(new EndpointInfo(parts[1], port));
                }
                return result;
            }

            int colon = code.LastIndexOf(':');
            if (colon > 0 && int.TryParse(code[(colon + 1)..], out int rawPort))
                result.Add(new EndpointInfo(code[..colon], rawPort));
        }
        catch { }
        return result;
    }

    private static string? GetLocalIpv4()
    {
        try
        {
            return NetworkInterface.GetAllNetworkInterfaces()
                .Where(n => n.OperationalStatus == OperationalStatus.Up && n.NetworkInterfaceType != NetworkInterfaceType.Loopback)
                .SelectMany(n => n.GetIPProperties().UnicastAddresses)
                .Select(a => a.Address)
                .FirstOrDefault(a => a.AddressFamily == AddressFamily.InterNetwork && !IPAddress.IsLoopback(a))
                ?.ToString();
        }
        catch { return null; }
    }

    private static async Task<string?> GetPublicIpAsync(CancellationToken ct)
    {
        try
        {
            using var timeout = CancellationTokenSource.CreateLinkedTokenSource(ct);
            timeout.CancelAfter(TimeSpan.FromSeconds(1.5));
            using var http = new HttpClient { Timeout = TimeSpan.FromSeconds(1.5) };
            string text = (await http.GetStringAsync("https://api.ipify.org", timeout.Token)).Trim();
            return IPAddress.TryParse(text, out var ip) && ip.AddressFamily == AddressFamily.InterNetwork ? text : null;
        }
        catch { return null; }
    }

    private static void TryOpenUpnpPort(int port, string localIp)
    {
        try
        {
            Type? type = Type.GetTypeFromProgID("HNetCfg.NATUPnP");
            if (type is null) return;
            dynamic? nat = Activator.CreateInstance(type);
            dynamic? mappings = nat?.StaticPortMappingCollection;
            if (mappings is null) return;
            try { mappings.Add(port, "TCP", port, localIp, true, "RiuClicker Lobby"); } catch { }
        }
        catch { }
    }

    public async ValueTask DisposeAsync()
    {
        await StopAsync();
        _clientSendLock.Dispose();
    }
}
