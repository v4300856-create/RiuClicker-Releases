from pathlib import Path

root = Path('src')

def rw(name):
    p = root / name
    return p, p.read_text(encoding='utf-8')

def save(p, s):
    p.write_text(s, encoding='utf-8')

# Keep this release on the free-v1.0 page while carrying the refreshed engine/UI.
p, s = rw('RiuClickerCS.csproj')
s = s.replace('<Version>1.1.0</Version>', '<Version>1.0.1</Version>')
s = s.replace('<AssemblyVersion>1.1.0.0</AssemblyVersion>', '<AssemblyVersion>1.0.1.0</AssemblyVersion>')
s = s.replace('<FileVersion>1.1.0.0</FileVersion>', '<FileVersion>1.0.1.0</FileVersion>')
save(p, s)

# High-speed clicker: preserve the absolute-deadline scheduler from cps520,
# add 1 ms Windows timer resolution for the whole click loop, and make sure
# Burst mode cannot accidentally turn a 500 CPS target into a ~10 CPS stream.
p, s = rw('Engines.cs')
if 'timeBeginPeriod' not in s:
    s = s.replace('using System.Diagnostics;\n', 'using System.Diagnostics;\nusing System.Runtime.InteropServices;\n')
    marker = 'public sealed class ClickerEngine\n{\n'
    helper = '''public sealed class ClickerEngine\n{\n    [DllImport("winmm.dll")] private static extern uint timeBeginPeriod(uint uPeriod);\n    [DllImport("winmm.dll")] private static extern uint timeEndPeriod(uint uPeriod);\n'''
    if marker not in s:
        raise SystemExit('ClickerEngine marker missing')
    s = s.replace(marker, helper, 1)

# Apply timer resolution only while a clicker worker is alive.
needle = '''    private async Task Loop(ClickerSettings settings, Func<string, CoordinateItem?> resolver, CancellationToken token)\n    {\n        try\n        {\n'''
replacement = '''    private async Task Loop(ClickerSettings settings, Func<string, CoordinateItem?> resolver, CancellationToken token)\n    {\n        timeBeginPeriod(1);\n        try\n        {\n'''
if needle in s:
    s = s.replace(needle, replacement, 1)
elif 'timeBeginPeriod(1);' not in s:
    raise SystemExit('Loop timer insertion target missing')

# At 100+ CPS the requested CPS is treated as an exact-speed mode.
# Burst pauses are for low-speed/humanized clicking only.
s = s.replace('if (settings.BurstEnabled && burstCounter >= Math.Max(1, settings.BurstSize))',
              'if (settings.BurstEnabled && NormalizeCps(settings.Cps) < 100 && burstCounter >= Math.Max(1, settings.BurstSize))')

# End timer period in the existing finally block.
old_finally = '''        finally\n        {\n            Running = false;\n            CountChanged?.Invoke(ClickCount);\n            RunningChanged?.Invoke(false);\n        }\n'''
new_finally = '''        finally\n        {\n            timeEndPeriod(1);\n            Running = false;\n            CountChanged?.Invoke(ClickCount);\n            RunningChanged?.Invoke(false);\n        }\n'''
if old_finally in s:
    s = s.replace(old_finally, new_finally, 1)
elif 'timeEndPeriod(1);' not in s:
    raise SystemExit('Loop timer cleanup target missing')
save(p, s)

# Show generated CPS in the UI so the user can verify the engine directly.
p, s = rw('MainWindow.xaml.cs')
old_stats = 'stats.Text = $"{engine.ClickCount:N0} {T("кликов")} · {elapsed:mm\\:ss}";'
new_stats = '''var actualCps = elapsed.TotalSeconds >= 0.25 ? engine.ClickCount / elapsed.TotalSeconds : 0;\n        stats.Text = $"{engine.ClickCount:N0} clicks · {elapsed:mm\\:ss} · {actualCps:0} CPS actual";'''
if old_stats in s:
    s = s.replace(old_stats, new_stats, 1)
elif 'CPS actual' not in s:
    raise SystemExit('runtime stats target missing')
save(p, s)

# Add an obvious 500 CPS preset to both clickers.
p, s = rw('MainWindow.xaml')
s = s.replace('<UniformGrid Columns="5" Margin="0,6,0,0"><Button Content="5" Style="{StaticResource RiuButton}" Margin="2" Click="QuickCps_Click" Tag="1|5"/><Button Content="10" Style="{StaticResource RiuButton}" Margin="2" Click="QuickCps_Click" Tag="1|10"/><Button Content="20" Style="{StaticResource RiuButton}" Margin="2" Click="QuickCps_Click" Tag="1|20"/><Button Content="50" Style="{StaticResource RiuButton}" Margin="2" Click="QuickCps_Click" Tag="1|50"/><Button Content="100" Style="{StaticResource RiuButton}" Margin="2" Click="QuickCps_Click" Tag="1|100"/></UniformGrid>',
'''<UniformGrid Columns="6" Margin="0,6,0,0"><Button Content="5" Style="{StaticResource RiuButton}" Margin="2" Click="QuickCps_Click" Tag="1|5"/><Button Content="10" Style="{StaticResource RiuButton}" Margin="2" Click="QuickCps_Click" Tag="1|10"/><Button Content="20" Style="{StaticResource RiuButton}" Margin="2" Click="QuickCps_Click" Tag="1|20"/><Button Content="50" Style="{StaticResource RiuButton}" Margin="2" Click="QuickCps_Click" Tag="1|50"/><Button Content="100" Style="{StaticResource RiuButton}" Margin="2" Click="QuickCps_Click" Tag="1|100"/><Button Content="500" Style="{StaticResource AccentButton}" Margin="2" Click="QuickCps_Click" Tag="1|500"/></UniformGrid>''')
s = s.replace('<UniformGrid Columns="5" Margin="0,6,0,0"><Button Content="5" Style="{StaticResource RiuButton}" Margin="2" Click="QuickCps_Click" Tag="2|5"/><Button Content="10" Style="{StaticResource RiuButton}" Margin="2" Click="QuickCps_Click" Tag="2|10"/><Button Content="20" Style="{StaticResource RiuButton}" Margin="2" Click="QuickCps_Click" Tag="2|20"/><Button Content="50" Style="{StaticResource RiuButton}" Margin="2" Click="QuickCps_Click" Tag="2|50"/><Button Content="100" Style="{StaticResource RiuButton}" Margin="2" Click="QuickCps_Click" Tag="2|100"/></UniformGrid>',
'''<UniformGrid Columns="6" Margin="0,6,0,0"><Button Content="5" Style="{StaticResource RiuButton}" Margin="2" Click="QuickCps_Click" Tag="2|5"/><Button Content="10" Style="{StaticResource RiuButton}" Margin="2" Click="QuickCps_Click" Tag="2|10"/><Button Content="20" Style="{StaticResource RiuButton}" Margin="2" Click="QuickCps_Click" Tag="2|20"/><Button Content="50" Style="{StaticResource RiuButton}" Margin="2" Click="QuickCps_Click" Tag="2|50"/><Button Content="100" Style="{StaticResource RiuButton}" Margin="2" Click="QuickCps_Click" Tag="2|100"/><Button Content="500" Style="{StaticResource AccentButton}" Margin="2" Click="QuickCps_Click" Tag="2|500"/></UniformGrid>''')
s = s.replace('Title="Free RiuClicker 1.1 · Pulse"', 'Title="Free RiuClicker 1.0 · Pulse Refresh"')
s = s.replace('Text="1.1  •  PULSE"', 'Text="1.0  •  PULSE REFRESH"')
s = s.replace('Text="FREE 1.1 · PULSE UI"', 'Text="FREE 1.0 · HIGH CPS REFRESH"')
save(p, s)

p, s = rw('BrandVisual.cs')
s = s.replace('Title = "Free RiuClicker 1.1 · Pulse";', 'Title = "Free RiuClicker 1.0 · Pulse Refresh";')
s = s.replace('HeaderBrandVersionText.Text = "PULSE UI  •  FREE 1.1";', 'HeaderBrandVersionText.Text = "PULSE UI  •  FREE 1.0 REFRESH";')
s = s.replace('SidebarBrandVersionText.Text = "1.1  •  PULSE";', 'SidebarBrandVersionText.Text = "1.0  •  HIGH CPS";')
save(p, s)

print('Free v1.0 high-CPS refresh applied')
