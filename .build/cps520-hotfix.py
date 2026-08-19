from pathlib import Path

# Remove the old 500 CPS clamps, make the slider effectively open-ended via
# auto-expansion, and replace coarse delay pacing with an absolute deadline
# scheduler so 500 CPS targets 2.000 ms periods without accumulating SendInput
# or Task.Delay drift.

p = Path('src/Engines.cs')
s = p.read_text(encoding='utf-8')
s = s.replace('var cps = Math.Clamp(settings.Cps, 0.1, 500);\n                var ms = 1000.0 / cps;', 'var cps = NormalizeCps(settings.Cps);\n                var ms = 1000.0 / cps;')
s = s.replace('''            var burstCounter = 0;\n            while (!token.IsCancellationRequested)\n            {\n''','''            var burstCounter = 0;\n            var nextClickTick = Stopwatch.GetTimestamp();\n            while (!token.IsCancellationRequested)\n            {\n''')
old_loop = '''                if (settings.BurstEnabled && burstCounter >= Math.Max(1, settings.BurstSize))\n                {\n                    burstCounter = 0;\n                    if (settings.BurstPauseMs > 0) await Task.Delay(settings.BurstPauseMs, token);\n                }\n\n                var cps = NormalizeCps(settings.Cps);\n                var ms = 1000.0 / cps;\n                if (settings.Humanize && settings.JitterPercent > 0)\n                {\n                    var span = ms * settings.JitterPercent / 100.0;\n                    ms += (_random.NextDouble() * 2 - 1) * span;\n                }\n                await ResponsiveDelay(ms, token);\n'''
new_loop = '''                if (settings.BurstEnabled && burstCounter >= Math.Max(1, settings.BurstSize))\n                {\n                    burstCounter = 0;\n                    if (settings.BurstPauseMs > 0)\n                    {\n                        await Task.Delay(settings.BurstPauseMs, token);\n                        nextClickTick = Stopwatch.GetTimestamp();\n                    }\n                }\n\n                var cps = NormalizeCps(settings.Cps);\n                var periodMs = 1000.0 / cps;\n                if (settings.Humanize && settings.JitterPercent > 0)\n                {\n                    var span = periodMs * settings.JitterPercent / 100.0;\n                    periodMs += (_random.NextDouble() * 2 - 1) * span;\n                }\n\n                // Absolute deadlines prevent SendInput overhead from lowering CPS.\n                nextClickTick += (long)Math.Max(1, periodMs * Stopwatch.Frequency / 1000.0);\n                var now = Stopwatch.GetTimestamp();\n                var periodTicks = Math.Max(1L, (long)(periodMs * Stopwatch.Frequency / 1000.0));\n                if (now - nextClickTick > periodTicks * 4) nextClickTick = now;\n                await WaitUntil(nextClickTick, token);\n'''
if old_loop not in s:
    raise SystemExit('click loop target not found')
s = s.replace(old_loop, new_loop)
old_delay = '''    // Keeps the UI responsive and avoids the large accumulated drift of a\n    // pure integer Task.Delay at ordinary CPS values. At very high CPS we do\n    // not spin a CPU core: the scheduler-friendly 1ms wait is retained.\n    private static async Task ResponsiveDelay(double milliseconds, CancellationToken token)\n    {\n        milliseconds = Math.Max(1, milliseconds);\n        if (milliseconds < 7)\n        {\n            await Task.Delay(Math.Max(1, (int)Math.Round(milliseconds)), token);\n            return;\n        }\n        var sw = Stopwatch.StartNew();\n        var coarse = Math.Max(1, (int)Math.Floor(milliseconds) - 2);\n        await Task.Delay(coarse, token);\n        while (sw.Elapsed.TotalMilliseconds < milliseconds)\n        {\n            token.ThrowIfCancellationRequested();\n            Thread.Yield();\n        }\n    }\n'''
new_delay = '''    private static double NormalizeCps(double cps)\n        => double.IsFinite(cps) && cps > 0 ? Math.Max(0.1, cps) : 0.1;\n\n    // High-resolution deadline wait. Sub-3 ms periods finish with SpinWait,\n    // which is what allows a 500 CPS setting to target a real 2 ms cadence.\n    private static async Task WaitUntil(long targetTicks, CancellationToken token)\n    {\n        while (true)\n        {\n            token.ThrowIfCancellationRequested();\n            var remainingTicks = targetTicks - Stopwatch.GetTimestamp();\n            if (remainingTicks <= 0) return;\n\n            var remainingMs = remainingTicks * 1000.0 / Stopwatch.Frequency;\n            if (remainingMs >= 3.0)\n            {\n                await Task.Delay(Math.Max(1, (int)Math.Floor(remainingMs - 1.0)), token);\n                continue;\n            }\n\n            var spinner = new SpinWait();\n            while (Stopwatch.GetTimestamp() < targetTicks)\n            {\n                token.ThrowIfCancellationRequested();\n                spinner.SpinOnce();\n            }\n            return;\n        }\n    }\n'''
if old_delay not in s:
    raise SystemExit('delay target not found')
s = s.replace(old_delay, new_delay)
p.write_text(s, encoding='utf-8')

p = Path('src/MainWindow.xaml.cs')
s = p.read_text(encoding='utf-8')
old = "c.Cps = Math.Clamp(cps, .1, 500); if (Math.Abs((slot == 1 ? C1CpsSlider : C2CpsSlider).Value - c.Cps) > .05) (slot == 1 ? C1CpsSlider : C2CpsSlider).Value = c.Cps;"
new = "c.Cps = double.IsFinite(cps) && cps > 0 ? Math.Max(.1, cps) : .1; var slider = slot == 1 ? C1CpsSlider : C2CpsSlider; if (c.Cps > slider.Maximum) slider.Maximum = Math.Ceiling(c.Cps / 500.0) * 500.0; if (Math.Abs(slider.Value - c.Cps) > .05) slider.Value = c.Cps;"
if old not in s:
    raise SystemExit('textbox CPS clamp target not found')
p.write_text(s.replace(old, new), encoding='utf-8')

p = Path('src/Models.cs')
s = p.read_text(encoding='utf-8')
old = 'c.Cps = Math.Clamp(c.Cps, 0.1, 500);'
new = 'c.Cps = double.IsFinite(c.Cps) && c.Cps > 0 ? Math.Max(0.1, c.Cps) : 12;'
if old not in s:
    raise SystemExit('settings CPS clamp target not found')
p.write_text(s.replace(old, new), encoding='utf-8')

p = Path('src/MainWindow.xaml')
s = p.read_text(encoding='utf-8')
s = s.replace('Minimum="1" Maximum="500" ValueChanged="CpsSlider_Changed" Tag="1"', 'Minimum="1" Maximum="5000" ValueChanged="CpsSlider_Changed" Tag="1"')
s = s.replace('Minimum="1" Maximum="500" ValueChanged="CpsSlider_Changed" Tag="2"', 'Minimum="1" Maximum="5000" ValueChanged="CpsSlider_Changed" Tag="2"')
p.write_text(s, encoding='utf-8')

p = Path('src/InputService.cs')
s = p.read_text(encoding='utf-8')
old = '        SendMouse(down, 0, 0, data);\n        SendMouse(up, 0, 0, data);\n'
new = '        SendMouseClick(down, up, data);\n'
if old not in s:
    raise SystemExit('mouse click target not found')
s = s.replace(old, new)
needle = '    private static void SendMouse(uint flags, int dx, int dy, uint data)\n'
helper = '''    private static void SendMouseClick(uint down, uint up, uint data)\n    {\n        var inputs = new[]\n        {\n            new INPUT { type = 0, U = new InputUnion { mi = new MOUSEINPUT { dx = 0, dy = 0, mouseData = data, dwFlags = down, dwExtraInfo = Marker } } },\n            new INPUT { type = 0, U = new InputUnion { mi = new MOUSEINPUT { dx = 0, dy = 0, mouseData = data, dwFlags = up, dwExtraInfo = Marker } } }\n        };\n        SendInput((uint)inputs.Length, inputs, Marshal.SizeOf<INPUT>());\n    }\n\n'''
if needle not in s:
    raise SystemExit('SendMouse helper insertion point missing')
s = s.replace(needle, helper + needle)
p.write_text(s, encoding='utf-8')

print('Applied unlimited CPS + high-resolution scheduler hotfix')
