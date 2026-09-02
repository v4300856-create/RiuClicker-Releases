from pathlib import Path
import re

root=Path("src")

# ---------- Clicker engine: snapshot settings + generation-safe state ----------
p=root/"Engines.cs"
s=p.read_text(encoding="utf-8")

start=s.find("public sealed class ClickerEngine")
end=s.find("public sealed class MacroEngine")
if start < 0 or end < 0 or end <= start:
    raise SystemExit("ClickerEngine block not found")

clicker=r'''public sealed class ClickerEngine
{
    private readonly object _sync = new();
    private CancellationTokenSource? _cts;
    private readonly Random _random = new();
    private int _generation;

    public bool Running { get; private set; }
    public long ClickCount { get; private set; }
    public DateTime? StartedAt { get; private set; }
    public event Action<bool>? RunningChanged;
    public event Action<long>? CountChanged;
    public event Action<string>? Message;

    public bool Start(ClickerSettings settings, Func<string, CoordinateItem?> coordinateResolver)
    {
        var snapshot = Snapshot(settings);
        if (!CanClick(snapshot, coordinateResolver, out var error))
        {
            Message?.Invoke(error);
            return false;
        }

        CancellationTokenSource cts;
        int generation;
        lock (_sync)
        {
            if (Running) return false;
            _cts?.Dispose();
            cts = new CancellationTokenSource();
            _cts = cts;
            generation = ++_generation;
            Running = true;
            ClickCount = 0;
            StartedAt = DateTime.Now;
        }

        RunningChanged?.Invoke(true);
        _ = Task.Run(() => Loop(snapshot, coordinateResolver, cts, generation));
        return true;
    }

    public bool TestSingleClick(ClickerSettings settings, Func<string, CoordinateItem?> coordinateResolver)
    {
        var snapshot = Snapshot(settings);
        if (!CanClick(snapshot, coordinateResolver, out var error))
        {
            Message?.Invoke(error);
            return false;
        }
        if (!PerformClick(snapshot, coordinateResolver))
        {
            Message?.Invoke("Координата недоступна — клик отменён");
            return false;
        }
        Message?.Invoke("Тестовый клик выполнен");
        return true;
    }

    public void Stop(string reason = "Остановлен")
    {
        CancellationTokenSource? cts;
        lock (_sync)
        {
            if (!Running) return;
            cts = _cts;
        }
        Message?.Invoke(reason);
        try { cts?.Cancel(); } catch { }
    }

    private async Task Loop(ClickerSettings settings, Func<string, CoordinateItem?> resolver, CancellationTokenSource ownedCts, int generation)
    {
        var token = ownedCts.Token;
        try
        {
            if (settings.StartDelayMs > 0) await Task.Delay(settings.StartDelayMs, token);
            var burstCounter = 0;
            var nextClickTick = Stopwatch.GetTimestamp();

            while (!token.IsCancellationRequested)
            {
                if (settings.ClickLimit > 0 && ClickCount >= settings.ClickLimit)
                {
                    Message?.Invoke($"Лимит достигнут: {settings.ClickLimit}");
                    break;
                }

                if (!PerformClick(settings, resolver))
                {
                    // Coordinate mode can stop only when the selected coordinate truly vanished.
                    Message?.Invoke("Координата стала недоступна — кликер остановлен");
                    break;
                }

                ClickCount++;
                burstCounter++;
                if (ClickCount % 5 == 0) CountChanged?.Invoke(ClickCount);

                if (settings.BurstEnabled && burstCounter >= Math.Max(1, settings.BurstSize))
                {
                    burstCounter = 0;
                    if (settings.BurstPauseMs > 0)
                    {
                        await Task.Delay(settings.BurstPauseMs, token);
                        nextClickTick = Stopwatch.GetTimestamp();
                    }
                }

                var cps = NormalizeCps(settings.Cps);
                var periodMs = 1000.0 / cps;
                if (settings.Humanize && settings.JitterPercent > 0)
                {
                    var span = periodMs * settings.JitterPercent / 100.0;
                    periodMs += (_random.NextDouble() * 2 - 1) * span;
                }

                nextClickTick += (long)Math.Max(1, periodMs * Stopwatch.Frequency / 1000.0);
                var now = Stopwatch.GetTimestamp();
                var periodTicks = Math.Max(1L, (long)(periodMs * Stopwatch.Frequency / 1000.0));
                if (now - nextClickTick > periodTicks * 4) nextClickTick = now;
                await WaitUntil(nextClickTick, token);
            }
        }
        catch (OperationCanceledException) { }
        catch (Exception ex)
        {
            // Do not silently die: report the exact reason.
            Message?.Invoke("Ошибка кликера: " + ex.Message);
        }
        finally
        {
            var notify = false;
            lock (_sync)
            {
                // A stale loop must never turn off a newer run.
                if (generation == _generation && ReferenceEquals(_cts, ownedCts))
                {
                    Running = false;
                    _cts = null;
                    notify = true;
                }
            }
            try { ownedCts.Dispose(); } catch { }
            if (notify)
            {
                CountChanged?.Invoke(ClickCount);
                RunningChanged?.Invoke(false);
            }
        }
    }

    private static ClickerSettings Snapshot(ClickerSettings s) => new()
    {
        Cps = s.Cps,
        MouseButton = s.MouseButton,
        Activation = s.Activation,
        Hotkey = s.Hotkey,
        Humanize = s.Humanize,
        JitterPercent = s.JitterPercent,
        ClickLimit = s.ClickLimit,
        ClickMode = s.ClickMode,
        SelectedCoordinateId = s.SelectedCoordinateId,
        StartDelayMs = s.StartDelayMs,
        BurstEnabled = s.BurstEnabled,
        BurstSize = s.BurstSize,
        BurstPauseMs = s.BurstPauseMs
    };

    private static bool CanClick(ClickerSettings settings, Func<string, CoordinateItem?> coordinateResolver, out string error)
    {
        error = "";
        if (settings.ClickMode != "coordinate") return true;
        if (string.IsNullOrWhiteSpace(settings.SelectedCoordinateId))
        {
            error = "Выбран режим координаты, но точка не выбрана";
            return false;
        }
        var coord = coordinateResolver(settings.SelectedCoordinateId);
        if (coord?.X is not int || coord.Y is not int)
        {
            error = "Выбранная координата ещё не сохранена";
            return false;
        }
        return true;
    }

    private static bool PerformClick(ClickerSettings settings, Func<string, CoordinateItem?> resolver)
    {
        if (settings.ClickMode == "coordinate")
        {
            if (string.IsNullOrWhiteSpace(settings.SelectedCoordinateId)) return false;
            var coord = resolver(settings.SelectedCoordinateId);
            if (coord?.X is not int x || coord.Y is not int y) return false;
            var old = InputService.CursorPosition();
            InputService.SetCursor(x, y);
            try { InputService.MouseClick(settings.MouseButton); }
            finally { InputService.SetCursor(old.X, old.Y); }
            return true;
        }
        InputService.MouseClick(settings.MouseButton);
        return true;
    }

    private static double NormalizeCps(double cps)
        => double.IsFinite(cps) && cps > 0 ? Math.Max(0.1, cps) : 0.1;

    private static async Task WaitUntil(long targetTicks, CancellationToken token)
    {
        while (true)
        {
            token.ThrowIfCancellationRequested();
            var remainingTicks = targetTicks - Stopwatch.GetTimestamp();
            if (remainingTicks <= 0) return;
            var remainingMs = remainingTicks * 1000.0 / Stopwatch.Frequency;
            if (remainingMs >= 3.0)
            {
                await Task.Delay(Math.Max(1, (int)Math.Floor(remainingMs - 1.0)), token);
                continue;
            }

            var spinner = new SpinWait();
            while (Stopwatch.GetTimestamp() < targetTicks)
            {
                token.ThrowIfCancellationRequested();
                spinner.SpinOnce();
            }
            return;
        }
    }
}

'''
s=s[:start]+clicker+s[end:]
p.write_text(s,encoding="utf-8")

# ---------- Bolts: make every V physically visible long enough ----------
p=root/"MainWindow.Bolts.cs"
if not p.exists():
    raise SystemExit("MainWindow.Bolts.cs missing")
s=p.read_text(encoding="utf-8")

# Strong minimums regardless of selected mode.
s=re.sub(r'var hold = Math\.Max\(\d+, t\.KeyHold\);', 'var hold = Math.Max(8, t.KeyHold);', s)
s=re.sub(r'var gap = Math\.Max\(\d+, t\.StepGap\);', 'var gap = Math.Max(12, t.StepGap);', s)

# Pre-release barrier before VVV.
s=s.replace('InputService.KeyUp("V");\n        await BoltDelay(3);',
            'InputService.KeyUp("V");\n        await BoltDelay(10);')

# Replace speed timings with reliable values; speed modes remain, but no 1-3 ms taps.
s=s.replace('"turbo" => new(5,10,3,8,6,12,14,6),',
            '"turbo" => new(10,12,12,8,10,12,14,6),')
s=s.replace('"instant" => new(3,4,2,7,5,10,14,6),',
            '"instant" => new(8,8,12,7,10,10,14,6),')
s=s.replace('_ => new(10,24,7,10,8,10,14,6)',
            '_ => new(12,24,12,10,12,10,14,6)')

p.write_text(s,encoding="utf-8")
print("stability fix applied")
