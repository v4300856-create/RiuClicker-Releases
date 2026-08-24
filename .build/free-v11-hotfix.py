from pathlib import Path

root = Path('src')

def rw(name):
    p = root / name
    return p, p.read_text(encoding='utf-8')

def save(p, s):
    p.write_text(s, encoding='utf-8')

def rep(s, old, new):
    return s.replace(old, new) if old in s else s

# ---------- RELIABLE MACRO CLICKS ----------
p, s = rw('InputService.cs')
if 'MouseClickHeld(' not in s:
    marker = '    public static void MoveMouseRelative(int dx, int dy)'
    if marker not in s:
        raise SystemExit('InputService marker missing')
    method = '''    public static void MouseClickHeld(string button, int holdMs, CancellationToken token)\n    {\n        button = button.ToLowerInvariant();\n        var (down, up, data) = button switch\n        {\n            \"right\" or \"mouse2\" => (0x0008u, 0x0010u, 0u),\n            \"middle\" or \"mouse3\" => (0x0020u, 0x0040u, 0u),\n            \"x1\" or \"mouse4\" => (0x0080u, 0x0100u, 1u),\n            \"x2\" or \"mouse5\" => (0x0080u, 0x0100u, 2u),\n            _ => (0x0002u, 0x0004u, 0u)\n        };\n\n        SendMouse(down, 0, 0, data);\n        var ms = Math.Clamp(holdMs, 6, 24);\n        if (token.WaitHandle.WaitOne(ms))\n        {\n            SendMouse(up, 0, 0, data);\n            token.ThrowIfCancellationRequested();\n            return;\n        }\n        SendMouse(up, 0, 0, data);\n    }\n\n'''
    s = s.replace(marker, method + marker)
save(p, s)

p, s = rw('Engines.cs')
old_mouse = '                InputService.MouseClick(step.Button);'
new_mouse = '                InputService.MouseClickHeld(step.Button, macro.SpeedMode == "fast" ? 10 : 14, token);'
if old_mouse in s:
    s = s.replace(old_mouse, new_mouse)
elif new_mouse not in s:
    raise SystemExit('Macro mouse step target missing')

old_coord = '        InputService.MouseClick(button);'
new_coord = '''        InputService.MouseClickHeld(button, settleMs <= 14 ? 10 : 14, token);\n        if (settleMs <= 14) await Task.Delay(6, token);'''
# only the macro coordinate helper occurrence should remain after the clicker engine section.
pos = s.rfind(old_coord)
if pos >= 0:
    s = s[:pos] + new_coord + s[pos + len(old_coord):]
elif 'InputService.MouseClickHeld(button, settleMs <= 14 ? 10 : 14, token);' not in s:
    raise SystemExit('Final coordinate click target missing')

# Fast stays fast, but gives games a slightly safer key/pointer envelope.
s = rep(s,
'''            _ => (12, 35, 8, 12)''',
'''            _ => (14, 38, 8, 14)''')
save(p, s)

# ---------- FREE 1.1 VERSION / BRANDING ----------
p, s = rw('RiuClickerCS.csproj')
s = rep(s, '<Version>1.0.0</Version>', '<Version>1.1.0</Version>')
s = rep(s, '<AssemblyVersion>1.0.0.0</AssemblyVersion>', '<AssemblyVersion>1.1.0.0</AssemblyVersion>')
s = rep(s, '<FileVersion>1.0.0.0</FileVersion>', '<FileVersion>1.1.0.0</FileVersion>')
save(p, s)

p, s = rw('Models.cs')
s = rep(s, 'public const string DefaultIntro = "Free RiuClicker";', 'public const string DefaultIntro = "Free RiuClicker 1.1";')
save(p, s)

p, s = rw('BrandVisual.cs')
s = rep(s, 'Title = "Free RiuClicker";', 'Title = "Free RiuClicker 1.1 · Pulse";')
s = rep(s, 'HeaderBrandVersionText.Text = "FREE EDITION";', 'HeaderBrandVersionText.Text = "PULSE UI  •  FREE 1.1";')
s = rep(s, 'SidebarBrandVersionText.Text = "FREE  •  RIUCLICKER";', 'SidebarBrandVersionText.Text = "1.1  •  PULSE";')
s = rep(s, 'SidebarBrandVisualHint.Text = "3D · FREE";', 'SidebarBrandVisualHint.Text = "FAST · CLEAN";')
save(p, s)

# ---------- PULSE UI PALETTE ----------
p, s = rw('App.xaml')
repls = {
    '<Color x:Key="AccentColor">#22D3EE</Color>': '<Color x:Key="AccentColor">#8B5CF6</Color>',
    '<SolidColorBrush x:Key="AccentSoftBrush" Color="#2422D3EE"/>': '<SolidColorBrush x:Key="AccentSoftBrush" Color="#268B5CF6"/>',
    '<SolidColorBrush x:Key="WindowBrush" Color="#070A10"/>': '<SolidColorBrush x:Key="WindowBrush" Color="#070810"/>',
    '<SolidColorBrush x:Key="SidebarBrush" Color="#090D14"/>': '<SolidColorBrush x:Key="SidebarBrush" Color="#0A0B16"/>',
    '<SolidColorBrush x:Key="CardBrush" Color="#101620"/>': '<SolidColorBrush x:Key="CardBrush" Color="#111421"/>',
    '<SolidColorBrush x:Key="CardHoverBrush" Color="#161E2A"/>': '<SolidColorBrush x:Key="CardHoverBrush" Color="#181C2D"/>',
    '<SolidColorBrush x:Key="ControlBrush" Color="#0B111A"/>': '<SolidColorBrush x:Key="ControlBrush" Color="#0D101B"/>',
    '<SolidColorBrush x:Key="ControlHoverBrush" Color="#121B28"/>': '<SolidColorBrush x:Key="ControlHoverBrush" Color="#171B2A"/>',
    '<SolidColorBrush x:Key="LineBrush" Color="#253142"/>': '<SolidColorBrush x:Key="LineBrush" Color="#31364B"/>',
    '<SolidColorBrush x:Key="LineSoftBrush" Color="#182230"/>': '<SolidColorBrush x:Key="LineSoftBrush" Color="#202437"/>',
    '<SolidColorBrush x:Key="TextBrush" Color="#F3F7FC"/>': '<SolidColorBrush x:Key="TextBrush" Color="#F7F7FF"/>',
    '<SolidColorBrush x:Key="MutedBrush" Color="#8795A8"/>': '<SolidColorBrush x:Key="MutedBrush" Color="#949AAF"/>',
    '<SolidColorBrush x:Key="DangerBrush" Color="#FF526D"/>': '<SolidColorBrush x:Key="DangerBrush" Color="#FB7185"/>',
    '<SolidColorBrush x:Key="SuccessBrush" Color="#44E2A1"/>': '<SolidColorBrush x:Key="SuccessBrush" Color="#4ADE80"/>',
    '<GradientStop Color="#2022D3EE" Offset="0"/>': '<GradientStop Color="#308B5CF6" Offset="0"/>',
    '<GradientStop Color="#081A8FFF" Offset="0.52"/>': '<GradientStop Color="#1822D3EE" Offset="0.52"/>',
    '<Setter Property="Height" Value="46"/>': '<Setter Property="Height" Value="48"/>',
    '<Setter Property="CornerRadius" Value="16"/>': '<Setter Property="CornerRadius" Value="18"/>',
    '<Setter Property="Padding" Value="18"/>': '<Setter Property="Padding" Value="20"/>',
    '<Setter Property="Background" Value="#151D28"/>': '<Setter Property="Background" Value="#17192A"/>',
    '<Setter Property="BorderBrush" Value="#34465A"/>': '<Setter Property="BorderBrush" Value="#514477"/>'
}
for old, new in repls.items():
    s = rep(s, old, new)
save(p, s)

# ---------- MAIN WINDOW POLISH ----------
p, s = rw('MainWindow.xaml')
ui_repls = {
    'Title="Free RiuClicker"': 'Title="Free RiuClicker 1.1 · Pulse"',
    'Text="FREE RIUCLICKER" FontSize="12.5"': 'Text="FREE RIUCLICKER" FontSize="13"',
    'Text="FREE  •  RIUCLICKER"': 'Text="1.1  •  PULSE"',
    'Text="NOVA CONTROL CENTER"': 'Text="PULSE CONTROL CENTER"',
    'Text="PHYSICAL HOTKEYS"': 'Text="LOW-LATENCY INPUT"',
    'Text="ОСНОВНОЕ"': 'Text="CONTROL"',
    'Text="ИНСТРУМЕНТЫ"': 'Text="TOOLS"',
    'Text="СИСТЕМА"': 'Text="STATUS"',
    'Text="Free edition"': 'Text="FREE 1.1 · PULSE UI"',
    'Text="FREE RIUCLICKER"': 'Text="FREE RIUCLICKER"'
}
for old, new in ui_repls.items():
    s = rep(s, old, new)
# Violet + cyan ambient glow instead of the old single-cyan look.
s = rep(s, '<GradientStop Color="#3522D3EE" Offset="0"/>', '<GradientStop Color="#408B5CF6" Offset="0"/>')
s = rep(s, '<GradientStop Color="#1022D3EE" Offset=".38"/>', '<GradientStop Color="#1822D3EE" Offset=".38"/>')
s = rep(s, 'Background="#24101823"', 'Background="#2A151329"')
s = rep(s, 'BorderBrush="#4F22D3EE"', 'BorderBrush="#668B5CF6"')
save(p, s)

print('Free RiuClicker 1.1 hotfix applied')
