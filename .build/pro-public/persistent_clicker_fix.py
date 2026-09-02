from pathlib import Path
import re

root=Path("src")
p=root/"Engines.cs"
s=p.read_text(encoding="utf-8")
start=s.find("public sealed class ClickerEngine")
end=s.find("public sealed class MacroEngine")
if start<0 or end<0: raise SystemExit("ClickerEngine not found")

clicker=r'''public sealed class ClickerEngine
{
    private readonly object _sync = new();
    private CancellationTokenSource? _cts;
    private readonly Random _random = new();
    private int _generation;
    private bool _desiredRunning;

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
            if (_desiredRunning) return false;
            _desiredRunning = true;
            _cts?.Dispose();
            cts = new CancellationTokenSource();
            _cts = cts;
            generation = ++_generation;
            Running = true;
            ClickCount = 0;
            StartedAt = DateTime.Now;
        }

        RunningChanged?.Invoke(true);
        _ = Task.Run(() => Supervisor(snapshot, coordinateResolver, cts, generation));
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
        return PerformClick(snapshot, coordinateResolver);
    }

    public void Stop(string reason = "Остановлен")
    {
        CancellationTokenSource? cts;
        lock (_sync)
        {
            if (!_desiredRunning && !Running) return;
            _desiredRunning = false;
            cts = _cts;
        }
        Message?.Invoke(reason);
        try { cts?.Cancel(); } catch { }
    }

    private async Task Supervisor(ClickerSettings settings, Func<string, CoordinateItem?> resolver, CancellationTokenSource ownedCts, int generation)
    {
        var token = ownedCts.Token;
        try
        {
            if (settings.StartDelayMs > 0)
                await Task.Delay(settings.StartDelayMs, token);

            while (true)
            {
                token.ThrowIfCancellationRequested();

                lock (_sync)
                    if (!_desiredRunning || generation != _generation) return;

                try
                {
                    await RunLoop(settings, resolver, token, generation);
                }
                catch (OperationCanceledException) { throw; }
                catch (Exception ex)
                {
                    Message?.Invoke("Кликер восстановлен после ошибки: " + ex.Message);
                    await Task.Delay(25, token);
                }

                lock (_sync)
                    if (!_desiredRunning || generation != _generation) return;

                // If the worker ever exits unexpectedly, immediately restore it.
                Message?.Invoke("Кликер автоматически продолжил работу");
                await Task.Delay(10, token);
            }
        }
        catch (OperationCanceledException) { }
        finally
        {
            bool notify=false;
            lock (_sync)
            {
                if (generation == _generation && ReferenceEquals(_cts, ownedCts))
                {
                    Running=false;
                    _desiredRunning=false;
                    _cts=null;
                    notify=true;
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

    private async Task RunLoop(ClickerSettings settings, Func<string, CoordinateItem?> resolver, CancellationToken token, int generation)
    {
        var burstCounter=0;
        var nextClickTick=Stopwatch.GetTimestamp();

        while (true)
        {
            token.ThrowIfCancellationRequested();
            lock (_sync)
                if (!_desiredRunning || generation != _generation) return;

            if (settings.ClickLimit > 0 && ClickCount >= settings.ClickLimit)
            {
                // A user-configured finite limit is the only non-manual automatic stop.
                lock (_sync) _desiredRunning=false;
                Message?.Invoke($"Лимит достигнут: {settings.ClickLimit}");
                return;
            }

            if (!PerformClick(settings, resolver))
            {
                // Never self-stop because a coordinate is temporarily unavailable.
                Message?.Invoke("Координата временно недоступна — ожидаю");
                await Task.Delay(50, token);
                continue;
            }

            ClickCount++;
            burstCounter++;
            if (ClickCount % 5 == 0) CountChanged?.Invoke(ClickCount);

            if (settings.BurstEnabled && burstCounter >= Math.Max(1, settings.BurstSize))
            {
                burstCounter=0;
                if (settings.BurstPauseMs > 0)
                {
                    await Task.Delay(settings.BurstPauseMs, token);
                    nextClickTick=Stopwatch.GetTimestamp();
                }
            }

            var cps=NormalizeCps(settings.Cps);
            var periodMs=1000.0/cps;
            if (settings.Humanize && settings.JitterPercent > 0)
            {
                var span=periodMs*settings.JitterPercent/100.0;
                periodMs += (_random.NextDouble()*2-1)*span;
            }

            nextClickTick += (long)Math.Max(1, periodMs*Stopwatch.Frequency/1000.0);
            var now=Stopwatch.GetTimestamp();
            var periodTicks=Math.Max(1L,(long)(periodMs*Stopwatch.Frequency/1000.0));
            if (now-nextClickTick > periodTicks*4) nextClickTick=now;
            await WaitUntil(nextClickTick,token);
        }
    }

    private static ClickerSettings Snapshot(ClickerSettings s) => new()
    {
        Cps=s.Cps, MouseButton=s.MouseButton, Activation=s.Activation, Hotkey=s.Hotkey,
        Humanize=s.Humanize, JitterPercent=s.JitterPercent, ClickLimit=s.ClickLimit,
        ClickMode=s.ClickMode, SelectedCoordinateId=s.SelectedCoordinateId,
        StartDelayMs=s.StartDelayMs, BurstEnabled=s.BurstEnabled,
        BurstSize=s.BurstSize, BurstPauseMs=s.BurstPauseMs
    };

    private static bool CanClick(ClickerSettings settings, Func<string, CoordinateItem?> resolver, out string error)
    {
        error="";
        if (settings.ClickMode!="coordinate") return true;
        if (string.IsNullOrWhiteSpace(settings.SelectedCoordinateId))
        {
            error="Выбран режим координаты, но точка не выбрана";
            return false;
        }
        var coord=resolver(settings.SelectedCoordinateId);
        if (coord?.X is not int || coord.Y is not int)
        {
            error="Выбранная координата ещё не сохранена";
            return false;
        }
        return true;
    }

    private static bool PerformClick(ClickerSettings settings, Func<string, CoordinateItem?> resolver)
    {
        if (settings.ClickMode=="coordinate")
        {
            if (string.IsNullOrWhiteSpace(settings.SelectedCoordinateId)) return false;
            var coord=resolver(settings.SelectedCoordinateId);
            if (coord?.X is not int x || coord.Y is not int y) return false;
            var old=InputService.CursorPosition();
            InputService.SetCursor(x,y);
            try { InputService.MouseClick(settings.MouseButton); }
            finally { InputService.SetCursor(old.X,old.Y); }
            return true;
        }
        InputService.MouseClick(settings.MouseButton);
        return true;
    }

    private static double NormalizeCps(double cps)
        => double.IsFinite(cps) && cps>0 ? Math.Max(0.1,cps) : 0.1;

    private static async Task WaitUntil(long targetTicks, CancellationToken token)
    {
        while (true)
        {
            token.ThrowIfCancellationRequested();
            var remainingTicks=targetTicks-Stopwatch.GetTimestamp();
            if (remainingTicks<=0) return;
            var remainingMs=remainingTicks*1000.0/Stopwatch.Frequency;
            if (remainingMs>=3.0)
            {
                await Task.Delay(Math.Max(1,(int)Math.Floor(remainingMs-1.0)),token);
                continue;
            }
            var spinner=new SpinWait();
            while (Stopwatch.GetTimestamp()<targetTicks)
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
print("persistent clicker supervisor applied")
