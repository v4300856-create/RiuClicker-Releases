from pathlib import Path

root = Path('src')
p = root / 'Engines.cs'
s = p.read_text(encoding='utf-8')

# Add WinMM timer resolution support for sub-10ms click intervals.
if 'internal static class HighResolutionTimer' not in s:
    s = s.replace('namespace RiuClickerCS;\n', '''namespace RiuClickerCS;\n\ninternal static class HighResolutionTimer\n{\n    [System.Runtime.InteropServices.DllImport("winmm.dll")]\n    private static extern uint timeBeginPeriod(uint uPeriod);\n    [System.Runtime.InteropServices.DllImport("winmm.dll")]\n    private static extern uint timeEndPeriod(uint uPeriod);\n\n    public static void Begin() { try { timeBeginPeriod(1); } catch { } }\n    public static void End() { try { timeEndPeriod(1); } catch { } }\n}\n''')

start = s.index('    private async Task Loop(ClickerSettings settings, Func<string, CoordinateItem?> resolver, CancellationToken token)')
end = s.index('\n    private static bool PerformClick', start)
new_loop = r'''    private async Task Loop(ClickerSettings settings, Func<string, CoordinateItem?> resolver, CancellationToken token)
    {
        var thread = Thread.CurrentThread;
        var oldPriority = thread.Priority;
        HighResolutionTimer.Begin();
        try
        {
            try { thread.Priority = ThreadPriority.AboveNormal; } catch { }
            if (settings.StartDelayMs > 0) await Task.Delay(settings.StartDelayMs, token);

            var burstCounter = 0;
            long nextTick = Stopwatch.GetTimestamp();
            long lastUiTick = nextTick;
            double frequency = Stopwatch.Frequency;

            while (!token.IsCancellationRequested)
            {
                if (settings.ClickLimit > 0 && ClickCount >= settings.ClickLimit) break;

                var cps = Math.Clamp(settings.Cps, 0.1, 500.0);
                var intervalMs = 1000.0 / cps;
                if (settings.Humanize && settings.JitterPercent > 0)
                {
                    var span = intervalMs * settings.JitterPercent / 100.0;
                    intervalMs += (_random.NextDouble() * 2 - 1) * span;
                    intervalMs = Math.Max(0.5, intervalMs);
                }
                long intervalTicks = Math.Max(1L, (long)(frequency * intervalMs / 1000.0));

                WaitUntil(nextTick, token);
                if (!PerformClick(settings, resolver))
                {
                    Message?.Invoke("Координата стала недоступна — кликер остановлен");
                    break;
                }

                ClickCount++;
                burstCounter++;

                long now = Stopwatch.GetTimestamp();
                if ((now - lastUiTick) * 1000.0 / frequency >= 50.0)
                {
                    CountChanged?.Invoke(ClickCount);
                    lastUiTick = now;
                }

                if (settings.BurstEnabled && burstCounter >= Math.Max(1, settings.BurstSize))
                {
                    burstCounter = 0;
                    if (settings.BurstPauseMs > 0)
                    {
                        await Task.Delay(settings.BurstPauseMs, token);
                        nextTick = Stopwatch.GetTimestamp() + intervalTicks;
                        continue;
                    }
                }

                nextTick += intervalTicks;

                // If Windows paused this thread for a long time, resume from now instead
                // of sending a huge burst of stale clicks. Small scheduler slips are retained
                // so the average rate remains close to the selected CPS.
                now = Stopwatch.GetTimestamp();
                if (now - nextTick > intervalTicks * 8)
                    nextTick = now;
            }
        }
        catch (OperationCanceledException) { }
        catch (Exception ex) { Message?.Invoke("Ошибка кликера: " + ex.Message); }
        finally
        {
            try { thread.Priority = oldPriority; } catch { }
            HighResolutionTimer.End();
            Running = false;
            CountChanged?.Invoke(ClickCount);
            RunningChanged?.Invoke(false);
        }
    }

    private static void WaitUntil(long targetTick, CancellationToken token)
    {
        double freq = Stopwatch.Frequency;
        while (true)
        {
            token.ThrowIfCancellationRequested();
            long now = Stopwatch.GetTimestamp();
            long remaining = targetTick - now;
            if (remaining <= 0) return;

            double remainingMs = remaining * 1000.0 / freq;
            if (remainingMs > 3.0)
            {
                Thread.Sleep(Math.Max(1, (int)remainingMs - 2));
            }
            else if (remainingMs > 0.8)
            {
                Thread.Yield();
            }
            else
            {
                Thread.SpinWait(80);
            }
        }
    }
'''
s = s[:start] + new_loop + s[end:]

# Remove obsolete scheduler-based delay helper if present.
marker = '    // Keeps the UI responsive and avoids the large accumulated drift of a\n'
if marker in s:
    a = s.index(marker)
    b = s.index('\n}\n\npublic sealed class MacroEngine', a)
    # Preserve ClickerEngine closing brace.
    s = s[:a] + s[b:]

p.write_text(s, encoding='utf-8')
print('Free v1.0 high CPS engine patch applied')
