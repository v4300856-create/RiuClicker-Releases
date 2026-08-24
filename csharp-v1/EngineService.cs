using System.Diagnostics;

namespace RiuClicker;

public sealed class EngineService : IAsyncDisposable
{
    private readonly AppSettings _settings;
    private readonly CancellationTokenSource _appCts = new();
    private readonly SemaphoreSlim _macroLock = new(1, 1);
    private readonly object _stateLock = new();
    private readonly Dictionary<int, bool> _keyState = new();
    private CancellationTokenSource? _clicker1Cts;
    private CancellationTokenSource? _clicker2Cts;
    private CancellationTokenSource _actionCts = new();
    private volatile bool _captureMode;
    private Task? _pollTask;

    public event Action<string, bool>? FeatureStateChanged;
    public event Action<string>? StatusChanged;
    public event Action? EmergencyStopped;

    public EngineService(AppSettings settings)
    {
        _settings = settings;
        _pollTask = Task.Run(() => PollLoopAsync(_appCts.Token));
    }

    public bool Clicker1Active => _clicker1Cts is not null;
    public bool Clicker2Active => _clicker2Cts is not null;

    private async Task PollLoopAsync(CancellationToken ct)
    {
        while (!ct.IsCancellationRequested)
        {
            try
            {
                if (!_captureMode)
                {
                    if (Pressed("F12")) StopAll();
                    if (Pressed(_settings.Clicker1.Hotkey)) ToggleClicker(1);
                    if (Pressed(_settings.Clicker2.Hotkey)) ToggleClicker(2);
                    if (_settings.BoltPush.Enabled && Pressed(_settings.BoltPush.Hotkey)) _ = RunMacroAsync(true);
                    if (_settings.Bolts.Enabled && Pressed(_settings.Bolts.Hotkey)) _ = RunMacroAsync(false);
                    if (Pressed(_settings.Wallhop.LeftHotkey)) _ = RunWallhopAsync(-1);
                    if (Pressed(_settings.Wallhop.RightHotkey)) _ = RunWallhopAsync(1);
                }
                await Task.Delay(4, ct);
            }
            catch (OperationCanceledException) { break; }
            catch (Exception ex)
            {
                StatusChanged?.Invoke("Engine: " + ex.Message);
                await Task.Delay(30, ct);
            }
        }
    }

    private bool Pressed(string key)
    {
        int vk = InputService.Vk(key);
        if (vk == 0) return false;
        bool down = InputService.IsDown(vk);
        bool previous;
        lock (_stateLock)
        {
            previous = _keyState.TryGetValue(vk, out var v) && v;
            _keyState[vk] = down;
        }
        return down && !previous;
    }

    public void ToggleClicker(int index)
    {
        if (index == 1)
        {
            if (_clicker1Cts is null) StartClicker(1);
            else StopClicker(1);
        }
        else
        {
            if (_clicker2Cts is null) StartClicker(2);
            else StopClicker(2);
        }
    }

    private void StartClicker(int index)
    {
        var settings = index == 1 ? _settings.Clicker1 : _settings.Clicker2;
        var cts = CancellationTokenSource.CreateLinkedTokenSource(_appCts.Token, _actionCts.Token);
        if (index == 1) _clicker1Cts = cts; else _clicker2Cts = cts;
        FeatureStateChanged?.Invoke($"clicker{index}", true);
        StatusChanged?.Invoke($"Clicker {index} ON");
        _ = Task.Run(() => ClickLoopAsync(index, settings, cts.Token));
    }

    private async Task ClickLoopAsync(int index, ClickerSettings settings, CancellationToken ct)
    {
        try
        {
            var sw = Stopwatch.StartNew();
            double next = 0;
            while (!ct.IsCancellationRequested)
            {
                double cps = Math.Clamp(settings.Cps, 1, 60);
                double interval = 1000.0 / cps;
                double now = sw.Elapsed.TotalMilliseconds;
                if (now >= next)
                {
                    InputService.Click(settings.MouseButton);
                    next = Math.Max(next + interval, now + Math.Min(2, interval));
                }
                int wait = (int)Math.Clamp(next - sw.Elapsed.TotalMilliseconds, 1, 8);
                await Task.Delay(wait, ct);
            }
        }
        catch (OperationCanceledException) { }
        finally
        {
            if (index == 1 && ReferenceEquals(_clicker1Cts?.Token, ct)) _clicker1Cts = null;
            if (index == 2 && ReferenceEquals(_clicker2Cts?.Token, ct)) _clicker2Cts = null;
        }
    }

    public void StopClicker(int index)
    {
        CancellationTokenSource? cts;
        if (index == 1) { cts = _clicker1Cts; _clicker1Cts = null; }
        else { cts = _clicker2Cts; _clicker2Cts = null; }
        try { cts?.Cancel(); cts?.Dispose(); } catch { }
        FeatureStateChanged?.Invoke($"clicker{index}", false);
        StatusChanged?.Invoke($"Clicker {index} OFF");
    }

    private async Task RunMacroAsync(bool boltPush)
    {
        var cfg = boltPush ? _settings.BoltPush : _settings.Bolts;
        var ct = _actionCts.Token;
        try
        {
            await _macroLock.WaitAsync(ct);
            try
            {
                var (hold, gap) = Timing(cfg.Speed);
                for (int i = 0; i < 3; i++)
                {
                    await InputService.Tap("V", hold, ct);
                    if (i < 2) await Task.Delay(gap, ct);
                }

                if (boltPush)
                {
                    await Task.Delay(gap, ct);
                    await InputService.Tap("SHIFT", hold + 2, ct);

                    if (cfg.ClickCoordinate)
                    {
                        var point = _settings.Coordinates.FirstOrDefault(x => x.Id == _settings.BoltPushCoordinateId);
                        if (point is not null)
                        {
                            await Task.Delay(gap, ct);
                            await InputService.ClickAtAsync(point.X, point.Y, "left", true, ct);
                        }
                    }
                }
                StatusChanged?.Invoke(boltPush ? "Bolt Push sent" : "Bolts sent");
            }
            finally { _macroLock.Release(); }
        }
        catch (OperationCanceledException) { }
        catch (Exception ex) { StatusChanged?.Invoke("Macro: " + ex.Message); }
    }

    private static (int Hold, int Gap) Timing(string speed) => (speed ?? "fast").ToLowerInvariant() switch
    {
        "instant" => (9, 7),
        "safe" => (24, 24),
        _ => (14, 12)
    };

    private async Task RunWallhopAsync(int direction)
    {
        var ct = _actionCts.Token;
        try
        {
            int pixels = Math.Clamp(_settings.Wallhop.Pixels, 50, 2000) * Math.Sign(direction);
            InputService.MoveRelative(pixels, 0);
            if (_settings.Wallhop.ReturnCamera)
            {
                await Task.Delay(Math.Clamp(_settings.Wallhop.ReturnDelayMs, 1, 250), ct);
                InputService.MoveRelative(-pixels, 0);
            }
            StatusChanged?.Invoke(direction < 0 ? "Wallhop LEFT" : "Wallhop RIGHT");
        }
        catch (OperationCanceledException) { }
    }

    public void StopAll()
    {
        StopClicker(1);
        StopClicker(2);
        try { _actionCts.Cancel(); _actionCts.Dispose(); } catch { }
        _actionCts = CancellationTokenSource.CreateLinkedTokenSource(_appCts.Token);
        InputService.KeyUp("V");
        InputService.KeyUp("SHIFT");
        EmergencyStopped?.Invoke();
        StatusChanged?.Invoke("F12 · ALL STOPPED");
    }

    public async Task<string> CaptureHotkeyAsync(CancellationToken ct = default)
    {
        if (_captureMode) throw new InvalidOperationException("Capture already active.");
        _captureMode = true;
        try
        {
            using var linked = CancellationTokenSource.CreateLinkedTokenSource(_appCts.Token, ct);
            await WaitAllReleasedAsync(linked.Token);
            while (!linked.IsCancellationRequested)
            {
                foreach (var item in InputService.CaptureKeys())
                {
                    if (InputService.IsDown(item.Vk))
                    {
                        while (InputService.IsDown(item.Vk)) await Task.Delay(6, linked.Token);
                        ResetEdges();
                        return item.Name;
                    }
                }
                await Task.Delay(5, linked.Token);
            }
            throw new OperationCanceledException();
        }
        finally { _captureMode = false; }
    }

    public async Task WaitForKeyAsync(string key, CancellationToken ct = default)
    {
        int vk = InputService.Vk(key);
        if (vk == 0) throw new ArgumentException("Unknown key", nameof(key));
        if (_captureMode) throw new InvalidOperationException("Capture already active.");
        _captureMode = true;
        try
        {
            using var linked = CancellationTokenSource.CreateLinkedTokenSource(_appCts.Token, ct);
            while (InputService.IsDown(vk)) await Task.Delay(5, linked.Token);
            while (!InputService.IsDown(vk)) await Task.Delay(5, linked.Token);
            while (InputService.IsDown(vk)) await Task.Delay(5, linked.Token);
            ResetEdges();
        }
        finally { _captureMode = false; }
    }

    private static async Task WaitAllReleasedAsync(CancellationToken ct)
    {
        while (InputService.CaptureKeys().Any(k => InputService.IsDown(k.Vk)))
            await Task.Delay(7, ct);
    }

    private void ResetEdges()
    {
        lock (_stateLock)
        {
            _keyState.Clear();
            foreach (var key in InputService.CaptureKeys()) _keyState[key.Vk] = InputService.IsDown(key.Vk);
        }
    }

    public async ValueTask DisposeAsync()
    {
        StopAll();
        _appCts.Cancel();
        try { if (_pollTask is not null) await _pollTask; } catch { }
        _macroLock.Dispose();
        _actionCts.Dispose();
        _appCts.Dispose();
    }
}
