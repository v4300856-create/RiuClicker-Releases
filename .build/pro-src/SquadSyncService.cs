using System.Net;
using System.Net.Sockets;
using System.Security.Cryptography;
using System.Text;

namespace RiuClickerCS;

public sealed class SquadSyncService : IAsyncDisposable
{
    private sealed class Peer
    {
        public required TcpClient Client { get; init; }
        public required StreamWriter Writer { get; init; }
        public required string Name { get; init; }
    }

    private readonly object _gate = new();
    private readonly List<Peer> _peers = [];
    private CancellationTokenSource? _cts;
    private TcpListener? _listener;
    private TcpClient? _client;
    private StreamWriter? _clientWriter;
    private int _mappedPort;
    private string _token = "";

    public bool IsHost { get; private set; }
    public bool IsConnected { get; private set; }
    public string JoinCode { get; private set; } = "";
    public int MemberCount { get { lock (_gate) return _peers.Count + (IsHost ? 1 : IsConnected ? 1 : 0); } }
    public string MembersText { get { lock (_gate) { var names = _peers.Select(x => x.Name).ToList(); if (IsHost) names.Insert(0, "Owner"); return names.Count == 0 ? "No members" : string.Join(", ", names); } } }

    public event Action<string>? StatusChanged;
    public event Action? MembersChanged;
    public event Action<string>? CommandReceived;

    public async Task<string> HostAsync(int port, string displayName, CancellationToken token = default)
    {
        await StopAsync();
        _cts = CancellationTokenSource.CreateLinkedTokenSource(token);
        port = Math.Clamp(port, 1024, 65535);
        _token = Convert.ToHexString(RandomNumberGenerator.GetBytes(12));

        var localIp = GetLanAddress();
        if (!TryMapUpnp(port, localIp))
            throw new InvalidOperationException("Could not open the lobby port with UPnP. Enable UPnP on the router or use the same local network.");

        _mappedPort = port;
        string publicIp;
        try
        {
            using var http = new HttpClient { Timeout = TimeSpan.FromSeconds(6) };
            publicIp = (await http.GetStringAsync("https://api.ipify.org", _cts.Token)).Trim();
            if (!IPAddress.TryParse(publicIp, out _)) throw new Exception();
        }
        catch
        {
            RemoveUpnpMapping();
            throw new InvalidOperationException("Could not determine the public IP for the lobby.");
        }

        _listener = new TcpListener(IPAddress.Any, port);
        _listener.Start();
        IsHost = true;
        IsConnected = true;
        JoinCode = EncodeJoinCode(publicIp, port, _token);
        StatusChanged?.Invoke("Squad online · Owner");
        MembersChanged?.Invoke();
        _ = AcceptLoopAsync(displayName, _cts.Token);
        return JoinCode;
    }

    public async Task JoinAsync(string joinCode, string displayName, CancellationToken token = default)
    {
        await StopAsync();
        var (host, port, tokenValue) = DecodeJoinCode(joinCode);
        _cts = CancellationTokenSource.CreateLinkedTokenSource(token);
        var tcp = new TcpClient { NoDelay = true };
        using var timeout = CancellationTokenSource.CreateLinkedTokenSource(_cts.Token);
        timeout.CancelAfter(TimeSpan.FromSeconds(8));
        await tcp.ConnectAsync(host, port, timeout.Token);
        var stream = tcp.GetStream();
        var reader = new StreamReader(stream, Encoding.UTF8, false, 1024, leaveOpen: true);
        var writer = new StreamWriter(stream, new UTF8Encoding(false), 1024, leaveOpen: true) { AutoFlush = true };
        await writer.WriteLineAsync($"HELLO|{tokenValue}|{SanitizeName(displayName)}");
        var welcome = await reader.ReadLineAsync(timeout.Token);
        if (welcome != "WELCOME")
        {
            tcp.Dispose();
            throw new InvalidOperationException("Lobby code was rejected by the owner.");
        }
        _client = tcp;
        _clientWriter = writer;
        IsConnected = true;
        IsHost = false;
        JoinCode = joinCode.Trim();
        StatusChanged?.Invoke("Squad online · Member");
        MembersChanged?.Invoke();
        _ = ClientReadLoopAsync(reader, _cts.Token);
    }

    public async Task BroadcastAsync(string command)
    {
        command = command.ToUpperInvariant();
        if (!IsHost || command is not ("E" or "V")) return;
        Peer[] peers;
        lock (_gate) peers = _peers.ToArray();
        foreach (var peer in peers)
        {
            try { await peer.Writer.WriteLineAsync("CMD|" + command); }
            catch { DropPeer(peer); }
        }
    }

    private async Task AcceptLoopAsync(string ownerName, CancellationToken token)
    {
        while (!token.IsCancellationRequested && _listener is not null)
        {
            TcpClient? tcp = null;
            try
            {
                tcp = await _listener.AcceptTcpClientAsync(token);
                tcp.NoDelay = true;
                _ = HandlePeerAsync(tcp, token);
            }
            catch (OperationCanceledException) { tcp?.Dispose(); break; }
            catch (Exception ex) { tcp?.Dispose(); StatusChanged?.Invoke("Squad accept error · " + ex.Message); }
        }
    }

    private async Task HandlePeerAsync(TcpClient tcp, CancellationToken token)
    {
        var stream = tcp.GetStream();
        var reader = new StreamReader(stream, Encoding.UTF8, false, 1024, leaveOpen: true);
        var writer = new StreamWriter(stream, new UTF8Encoding(false), 1024, leaveOpen: true) { AutoFlush = true };
        Peer? peer = null;
        try
        {
            using var helloTimeout = CancellationTokenSource.CreateLinkedTokenSource(token);
            helloTimeout.CancelAfter(TimeSpan.FromSeconds(7));
            var hello = await reader.ReadLineAsync(helloTimeout.Token);
            var parts = hello?.Split('|', 3) ?? [];
            if (parts.Length != 3 || parts[0] != "HELLO" || !CryptographicOperations.FixedTimeEquals(Encoding.UTF8.GetBytes(parts[1]), Encoding.UTF8.GetBytes(_token)))
            {
                await writer.WriteLineAsync("DENY");
                tcp.Dispose();
                return;
            }
            peer = new Peer { Client = tcp, Writer = writer, Name = SanitizeName(parts[2]) };
            lock (_gate) _peers.Add(peer);
            await writer.WriteLineAsync("WELCOME");
            MembersChanged?.Invoke();
            StatusChanged?.Invoke($"{peer.Name} joined the squad");
            while (!token.IsCancellationRequested && tcp.Connected)
            {
                var line = await reader.ReadLineAsync(token);
                if (line is null) break;
                if (line == "PING") await writer.WriteLineAsync("PONG");
            }
        }
        catch { }
        finally
        {
            if (peer is not null) DropPeer(peer); else tcp.Dispose();
        }
    }

    private async Task ClientReadLoopAsync(StreamReader reader, CancellationToken token)
    {
        try
        {
            while (!token.IsCancellationRequested)
            {
                var line = await reader.ReadLineAsync(token);
                if (line is null) break;
                if (line is "CMD|E" or "CMD|V") CommandReceived?.Invoke(line[^1].ToString());
            }
        }
        catch { }
        if (!token.IsCancellationRequested)
        {
            IsConnected = false;
            StatusChanged?.Invoke("Squad disconnected");
            MembersChanged?.Invoke();
        }
    }

    private void DropPeer(Peer peer)
    {
        lock (_gate) _peers.Remove(peer);
        try { peer.Client.Dispose(); } catch { }
        MembersChanged?.Invoke();
    }

    public async Task StopAsync()
    {
        var cts = _cts;
        _cts = null;
        try { cts?.Cancel(); } catch { }
        try { _listener?.Stop(); } catch { }
        _listener = null;
        Peer[] peers;
        lock (_gate) { peers = _peers.ToArray(); _peers.Clear(); }
        foreach (var p in peers) try { p.Client.Dispose(); } catch { }
        try { _client?.Dispose(); } catch { }
        _client = null;
        _clientWriter = null;
        RemoveUpnpMapping();
        IsHost = false;
        IsConnected = false;
        JoinCode = "";
        cts?.Dispose();
        MembersChanged?.Invoke();
        StatusChanged?.Invoke("Squad offline");
        await Task.CompletedTask;
    }

    public async ValueTask DisposeAsync() => await StopAsync();

    private static string SanitizeName(string? name)
    {
        var clean = new string((name ?? "Player").Where(c => char.IsLetterOrDigit(c) || c is ' ' or '_' or '-').Take(20).ToArray()).Trim();
        return string.IsNullOrWhiteSpace(clean) ? "Player" : clean;
    }

    private static string EncodeJoinCode(string ip, int port, string token)
    {
        var raw = Encoding.UTF8.GetBytes($"{ip}|{port}|{token}");
        return Convert.ToBase64String(raw).TrimEnd('=').Replace('+', '-').Replace('/', '_');
    }

    private static (string Host, int Port, string Token) DecodeJoinCode(string code)
    {
        try
        {
            var b64 = code.Trim().Replace('-', '+').Replace('_', '/');
            b64 += new string('=', (4 - b64.Length % 4) % 4);
            var raw = Encoding.UTF8.GetString(Convert.FromBase64String(b64));
            var p = raw.Split('|', 3);
            if (p.Length != 3 || !IPAddress.TryParse(p[0], out _) || !int.TryParse(p[1], out var port) || port is < 1024 or > 65535 || p[2].Length < 12) throw new Exception();
            return (p[0], port, p[2]);
        }
        catch { throw new InvalidOperationException("Invalid squad code."); }
    }

    private static string GetLanAddress()
    {
        using var udp = new UdpClient();
        udp.Connect("8.8.8.8", 65530);
        return ((IPEndPoint)udp.Client.LocalEndPoint!).Address.ToString();
    }

    private bool TryMapUpnp(int port, string localIp)
    {
        try
        {
            var type = Type.GetTypeFromProgID("HNetCfg.NATUPnP");
            if (type is null) return false;
            dynamic nat = Activator.CreateInstance(type)!;
            dynamic mappings = nat.StaticPortMappingCollection;
            if (mappings is null) return false;
            try { mappings.Remove(port, "TCP"); } catch { }
            mappings.Add(port, "TCP", port, localIp, true, "RiuClicker Pro Squad Sync");
            return true;
        }
        catch { return false; }
    }

    private void RemoveUpnpMapping()
    {
        if (_mappedPort == 0) return;
        try
        {
            var type = Type.GetTypeFromProgID("HNetCfg.NATUPnP");
            if (type is not null)
            {
                dynamic nat = Activator.CreateInstance(type)!;
                dynamic mappings = nat.StaticPortMappingCollection;
                if (mappings is not null) mappings.Remove(_mappedPort, "TCP");
            }
        }
        catch { }
        _mappedPort = 0;
    }
}
