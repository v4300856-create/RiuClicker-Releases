from pathlib import Path

root = Path('src')

def rw(name):
    p = root / name
    return p, p.read_text(encoding='utf-8')

def save(p, s):
    p.write_text(s, encoding='utf-8')

# ---- High CPS mouse packets ----
p, s = rw('InputService.cs')
if 'MouseClickRateSafe(' not in s:
    marker = '    public static void MoveMouseRelative(int dx, int dy)'
    if marker not in s:
        raise SystemExit('InputService insertion marker missing')
    helper = r'''    public static void MouseClickRateSafe(string button, double cps)
    {
        button = button.ToLowerInvariant();
        var (down, up, data) = button switch
        {
            "right" or "mouse2" => (0x0008u, 0x0010u, 0u),
            "middle" or "mouse3" => (0x0020u, 0x0040u, 0u),
            "x1" or "mouse4" => (0x0080u, 0x0100u, 1u),
            "x2" or "mouse5" => (0x0080u, 0x0100u, 2u),
            _ => (0x0002u, 0x0004u, 0u)
        };

        // At ordinary CPS the existing paired SendInput path is ideal.
        if (cps < 120)
        {
            SendMouseClick(down, up, data);
            return;
        }

        // Very fast DOWN+UP pairs can be collapsed/ignored by some games.
        // Keep the button physically down for a fraction of the target period,
        // while still leaving enough time to reach 500 CPS (2 ms period).
        SendMouse(down, 0, 0, data);
        var periodUs = 1_000_000.0 / Math.Max(1.0, cps);
        var holdUs = Math.Clamp(periodUs * 0.28, 220.0, 700.0);
        var until = Stopwatch.GetTimestamp() + (long)(holdUs * Stopwatch.Frequency / 1_000_000.0);
        var spin = new SpinWait();
        while (Stopwatch.GetTimestamp() < until) spin.SpinOnce();
        SendMouse(up, 0, 0, data);
    }

'''
    s = s.replace(marker, helper + marker, 1)
save(p, s)

# ---- Use rate-safe click path only for the autoclicker ----
p, s = rw('Engines.cs')
old_coord = '            try { InputService.MouseClick(settings.MouseButton); }'
new_coord = '            try { InputService.MouseClickRateSafe(settings.MouseButton, settings.Cps); }'
if old_coord in s:
    s = s.replace(old_coord, new_coord, 1)
elif new_coord not in s:
    raise SystemExit('coordinate click target missing')

old_cursor = '        InputService.MouseClick(settings.MouseButton);\n        return true;'
new_cursor = '        InputService.MouseClickRateSafe(settings.MouseButton, settings.Cps);\n        return true;'
if old_cursor in s:
    s = s.replace(old_cursor, new_cursor, 1)
elif new_cursor not in s:
    raise SystemExit('cursor click target missing')

# Give the high-CPS loop a dedicated long-running worker rather than a normal
# thread-pool work item. This avoids scheduler starvation around 2 ms periods.
old_start = '_ = Task.Run(() => Loop(settings, coordinateResolver, _cts.Token));'
new_start = '''_ = Task.Factory.StartNew(
            () => Loop(settings, coordinateResolver, _cts.Token).GetAwaiter().GetResult(),
            _cts.Token,
            TaskCreationOptions.LongRunning,
            TaskScheduler.Default);'''
if old_start in s:
    s = s.replace(old_start, new_start, 1)
elif 'TaskCreationOptions.LongRunning' not in s:
    raise SystemExit('clicker worker target missing')

# High-rate deadline wait: below 4 ms never yield back to the timer scheduler.
old_threshold = 'if (remainingMs >= 3.0)'
if old_threshold in s:
    s = s.replace(old_threshold, 'if (remainingMs >= 4.0)', 1)

save(p, s)

# ---- Keep requested public channel/tag as Free v1.0 ----
p, s = rw('RiuClickerCS.csproj')
s = s.replace('<Version>1.1.0</Version>', '<Version>1.0.1</Version>')
s = s.replace('<AssemblyVersion>1.1.0.0</AssemblyVersion>', '<AssemblyVersion>1.0.1.0</AssemblyVersion>')
s = s.replace('<FileVersion>1.1.0.0</FileVersion>', '<FileVersion>1.0.1.0</FileVersion>')
save(p, s)

p, s = rw('Models.cs')
s = s.replace('public const string DefaultIntro = "Free RiuClicker 1.1";', 'public const string DefaultIntro = "Free RiuClicker 1.0";')
save(p, s)

p, s = rw('BrandVisual.cs')
s = s.replace('Title = "Free RiuClicker 1.1 · Pulse";', 'Title = "Free RiuClicker 1.0 · Pulse";')
s = s.replace('HeaderBrandVersionText.Text = "PULSE UI  •  FREE 1.1";', 'HeaderBrandVersionText.Text = "PULSE UI  •  FREE 1.0";')
s = s.replace('SidebarBrandVersionText.Text = "1.1  •  PULSE";', 'SidebarBrandVersionText.Text = "1.0  •  PULSE";')
save(p, s)

print('Free v1.0 CPS500 hotfix applied')
