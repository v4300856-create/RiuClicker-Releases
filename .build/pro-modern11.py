from pathlib import Path
import re

root = Path('src')

def rw(name):
    p = root / name
    return p, p.read_text(encoding='utf-8')

def save(p, s):
    p.write_text(s, encoding='utf-8')

# -------- Hotkey capture reliability / TAB display --------
p, s = rw('MainWindow.Extras.cs')
old = '''    private void HotkeyCapture_Click(object sender, RoutedEventArgs e)\n    {\n        if (sender is not Button b || b.Tag is null) return;\n        _captureTarget = b.Tag.ToString();\n        GlobalStatusText.Text = T("Нажми физическую клавишу или Mouse4/Mouse5 · ESC отмена");\n    }\n'''
new = '''    private Button? _captureButton;\n\n    private static string HotkeyLabel(string? key)\n        => string.IsNullOrWhiteSpace(key) ? "NOT SET" : key.Trim().ToUpperInvariant() switch\n        {\n            "TAB" => "TAB",\n            "SPACE" => "SPACE",\n            "ESC" => "ESC",\n            var k => k\n        };\n\n    private void HotkeyCapture_Click(object sender, RoutedEventArgs e)\n    {\n        if (sender is not Button b || b.Tag is null) return;\n        _captureTarget = b.Tag.ToString();\n        _captureButton = b;\n        b.Content = "PRESS A KEY…";\n        GlobalStatusText.Text = "Hotkey capture · press any physical key (TAB supported) · ESC cancels";\n    }\n'''
if old not in s:
    raise SystemExit('HotkeyCapture_Click target not found')
s = s.replace(old, new, 1)

oldcap = '''        if (_captureTarget is not null)\n        {\n            if (key == "ESC") { _captureTarget = null; GlobalStatusText.Text = T("Назначение отменено"); return; }\n            AssignCapturedHotkey(_captureTarget, key);\n            _captureTarget = null;\n            return;\n        }\n'''
newcap = '''        if (_captureTarget is not null)\n        {\n            var target = _captureTarget;\n            if (key == "ESC")\n            {\n                _captureTarget = null;\n                _captureButton = null;\n                LoadClickerUi(1, _settings.Clicker1);\n                LoadClickerUi(2, _settings.Clicker2);\n                LoadWallhopUi();\n                RefreshCoordinateEditor();\n                RefreshMacroEditor();\n                RefreshProUi();\n                GlobalStatusText.Text = "Hotkey capture cancelled";\n                return;\n            }\n\n            // TAB is normally a WPF focus-navigation key. The low-level hook sees it\n            // first, so commit the physical key directly to the selected action and\n            // refresh the exact button label before normal focus navigation happens.\n            AssignCapturedHotkey(target, key);\n            _captureTarget = null;\n            _captureButton = null;\n            return;\n        }\n'''
if oldcap not in s:
    raise SystemExit('capture block target not found')
s = s.replace(oldcap, newcap, 1)

needle = '''        if (target == "clicker1") _settings.Clicker1.Hotkey = key;\n        else if (target == "clicker2") _settings.Clicker2.Hotkey = key;\n'''
rep = '''        if (target == "clicker1")\n        {\n            _settings.Clicker1.Hotkey = key;\n            C1HotkeyButton.Content = $"HOTKEY · {HotkeyLabel(key)}";\n        }\n        else if (target == "clicker2")\n        {\n            _settings.Clicker2.Hotkey = key;\n            C2HotkeyButton.Content = $"HOTKEY · {HotkeyLabel(key)}";\n        }\n'''
if needle not in s:
    raise SystemExit('assignment target not found')
s = s.replace(needle, rep, 1)
save(p, s)

p, s = rw('MainWindow.xaml.cs')
oldlabel = 'hotkey.Content = $"{T("ЗАПУСК")} · {(string.IsNullOrWhiteSpace(c.Hotkey) ? T("НЕ НАЗНАЧЕН") : c.Hotkey)}";'
newlabel = 'hotkey.Content = $"HOTKEY · {HotkeyLabel(c.Hotkey)}";'
if oldlabel not in s:
    raise SystemExit('LoadClickerUi hotkey label target not found')
s = s.replace(oldlabel, newlabel, 1)
save(p, s)

# -------- New FLUX 2026 visual system --------
p, s = rw('App.xaml')
s = s.replace('RIU 5.22 · NOVA CONTROL UI', 'RIUCLICKER PRO 1.1 · FLUX 2026 UI')
colors = {
    '#22D3EE': '#8B5CF6',
    '#2422D3EE': '#2D8B5CF6',
    '#070A10': '#05060A',
    '#090D14': '#080A10',
    '#101620': '#0E111A',
    '#161E2A': '#171B29',
    '#0B111A': '#0A0D14',
    '#121B28': '#141927',
    '#253142': '#2A3040',
    '#182230': '#1B2030',
    '#F3F7FC': '#F7F8FC',
    '#8795A8': '#929AAF',
    '#FF526D': '#FF5F7A',
    '#44E2A1': '#46E6B0',
}
for a,b in colors.items():
    s = s.replace(a,b)
s = s.replace('<GradientStop Color="#2022D3EE" Offset="0"/>', '<GradientStop Color="#3B8B5CF6" Offset="0"/>')
s = s.replace('<GradientStop Color="#081A8FFF" Offset="0.52"/>', '<GradientStop Color="#2022D3EE" Offset="0.55"/>')
s = s.replace('<Setter Property="Padding" Value="14,10"/>', '<Setter Property="Padding" Value="15,11"/>', 1)
s = s.replace('CornerRadius="12" Background="{DynamicResource AccentSoftBrush}" Opacity="0"', 'CornerRadius="15" Background="{DynamicResource AccentSoftBrush}" Opacity="0"', 1)
s = s.replace('CornerRadius="11"\n                                    Background="{TemplateBinding Background}"', 'CornerRadius="14"\n                                    Background="{TemplateBinding Background}"', 1)
s = s.replace('CornerRadius="10" Height="1" VerticalAlignment="Top"', 'CornerRadius="13" Height="1" VerticalAlignment="Top"', 1)
s = s.replace('<Setter Property="Height" Value="46"/>', '<Setter Property="Height" Value="48"/>', 1)
s = s.replace('<Setter Property="Margin" Value="0,3"/>', '<Setter Property="Margin" Value="0,4"/>', 1)
s = s.replace('<Setter Property="CornerRadius" Value="16"/>', '<Setter Property="CornerRadius" Value="20"/>', 1)
s = s.replace('<Setter Property="Padding" Value="18"/>', '<Setter Property="Padding" Value="20"/>', 1)
s = s.replace('<Setter Property="Background" Value="#151D28"/>', '<Setter Property="Background" Value="#C9121520"/>', 1)
s = s.replace('<Setter Property="BorderBrush" Value="#34465A"/>', '<Setter Property="BorderBrush" Value="#4A8B5CF6"/>', 1)
s = s.replace('<Setter Property="Padding" Value="20"/>', '<Setter Property="Padding" Value="22"/>', 1)
insert_before = '        <!-- Cards -->\n'
new_styles = '''        <Style TargetType="Border" x:Key="FluxPill">\n            <Setter Property="Background" Value="#24131A2B"/>\n            <Setter Property="BorderBrush" Value="#5B8B5CF6"/>\n            <Setter Property="BorderThickness" Value="1"/>\n            <Setter Property="CornerRadius" Value="999"/>\n            <Setter Property="Padding" Value="13,7"/>\n        </Style>\n\n'''
if insert_before not in s:
    raise SystemExit('App style insertion target missing')
s = s.replace(insert_before, new_styles + insert_before, 1)
save(p, s)

p, s = rw('MainWindow.xaml')
s = s.replace('Title="Riu Clicker 5.22 · Nova Control" Width="1180" Height="790" MinWidth="1000" MinHeight="660"',
              'Title="RiuClicker Pro 1.1 · Flux UI" Width="1280" Height="840" MinWidth="1060" MinHeight="700"')
s = s.replace('<Border x:Name="BackgroundOverlay" Background="#C8070A10"/>', '<Border x:Name="BackgroundOverlay" Background="#B505060A"/>')
old_orb = '''        <Ellipse Width="640" Height="640" HorizontalAlignment="Right" VerticalAlignment="Top" Margin="0,-360,-260,0"\n                 IsHitTestVisible="False" Opacity=".75">\n            <Ellipse.Fill>\n                <RadialGradientBrush>\n                    <GradientStop Color="#3522D3EE" Offset="0"/>\n                    <GradientStop Color="#1022D3EE" Offset=".38"/>\n                    <GradientStop Color="#00070A10" Offset="1"/>\n                </RadialGradientBrush>\n            </Ellipse.Fill>\n        </Ellipse>\n'''
new_orb = '''        <Ellipse Width="760" Height="760" HorizontalAlignment="Right" VerticalAlignment="Top" Margin="0,-430,-300,0" IsHitTestVisible="False" Opacity=".8">\n            <Ellipse.Fill><RadialGradientBrush><GradientStop Color="#508B5CF6" Offset="0"/><GradientStop Color="#168B5CF6" Offset=".42"/><GradientStop Color="#0005060A" Offset="1"/></RadialGradientBrush></Ellipse.Fill>\n        </Ellipse>\n        <Ellipse Width="560" Height="560" HorizontalAlignment="Left" VerticalAlignment="Bottom" Margin="-280,0,0,-310" IsHitTestVisible="False" Opacity=".62">\n            <Ellipse.Fill><RadialGradientBrush><GradientStop Color="#3022D3EE" Offset="0"/><GradientStop Color="#0B22D3EE" Offset=".44"/><GradientStop Color="#0005060A" Offset="1"/></RadialGradientBrush></Ellipse.Fill>\n        </Ellipse>\n'''
if old_orb in s:
    s = s.replace(old_orb, new_orb, 1)
else:
    start = s.find('        <Ellipse Width="640" Height="640"')
    end = s.find('        </Ellipse>', start)
    if start >= 0 and end >= 0:
        end += len('        </Ellipse>\n')
        s = s[:start] + new_orb + s[end:]

s = s.replace('<Grid.RowDefinitions><RowDefinition Height="50"/><RowDefinition Height="*"/></Grid.RowDefinitions>', '<Grid.RowDefinitions><RowDefinition Height="58"/><RowDefinition Height="*"/></Grid.RowDefinitions>', 1)
s = s.replace('Margin="16,0,10,0"', 'Margin="20,0,12,0"', 1)
s = s.replace('Text="NOVA CONTROL  •  5.22"', 'Text="PRO 1.1  •  FLUX UI"')
s = s.replace('Text="PRO 1.0  •  COMMAND CENTER"', 'Text="PRO 1.1  •  FLUX UI"')
s = s.replace('<Grid.ColumnDefinitions><ColumnDefinition Width="232"/><ColumnDefinition Width="*"/></Grid.ColumnDefinitions>', '<Grid.ColumnDefinitions><ColumnDefinition Width="248"/><ColumnDefinition Width="*"/></Grid.ColumnDefinitions>', 1)
s = s.replace('<Grid Grid.Column="1" Margin="24,18,24,20">', '<Grid Grid.Column="1" Margin="28,22,28,24">', 1)
s = s.replace('<Grid x:Name="PageHeaderPanel" Margin="2,0,2,16">', '<Grid x:Name="PageHeaderPanel" Margin="2,0,2,18">', 1)
s = s.replace('FontSize="29" FontWeight="Black"', 'FontSize="31" FontWeight="Black"', 1)
s = s.replace('<Border Grid.Column="1" CornerRadius="14" BorderBrush="#4F22D3EE" BorderThickness="1" Padding="13,8" VerticalAlignment="Center" Background="#24101823">\n                            <StackPanel Orientation="Horizontal"><TextBlock Text="●" Foreground="{DynamicResource SuccessBrush}" Margin="0,0,6,0"/><TextBlock Text="PHYSICAL HOTKEYS" FontSize="9" FontWeight="Bold"/></StackPanel>\n                        </Border>',
'''<Border Grid.Column="1" Style="{StaticResource FluxPill}" VerticalAlignment="Center">\n                            <StackPanel Orientation="Horizontal"><TextBlock Text="●" Foreground="{DynamicResource SuccessBrush}" Margin="0,0,7,0"/><TextBlock Text="FLUX ENGINE · ONLINE" FontSize="9" FontWeight="Bold"/></StackPanel>\n                        </Border>''')
s = s.replace('RIUCLICKER PRO · COMMAND CENTER', 'RIUCLICKER PRO · FLUX COMMAND CENTER')
s = s.replace('Text="АВТОКЛИКЕР 1"', 'Text="AUTO ENGINE 01"')
s = s.replace('Text="АВТОКЛИКЕР 2"', 'Text="AUTO ENGINE 02"')
s = s.replace('Content="ЗАПУСК · F8"', 'Content="HOTKEY · F8"')
s = s.replace('Content="ЗАПУСК · F9"', 'Content="HOTKEY · F9"')
clicker_anchor = '''                        <ScrollViewer x:Name="PageClicker" VerticalScrollBarVisibility="Auto">\n                            <StackPanel>\n                                <Grid>'''
clicker_new = '''                        <ScrollViewer x:Name="PageClicker" VerticalScrollBarVisibility="Auto">\n                            <StackPanel>\n                                <Border Style="{StaticResource HeroBorder}" Margin="0,0,0,14">\n                                    <Grid><Grid.ColumnDefinitions><ColumnDefinition/><ColumnDefinition Width="Auto"/></Grid.ColumnDefinitions>\n                                        <StackPanel><TextBlock Text="AUTOMATION DECK" FontSize="21" FontWeight="Black"/><TextBlock Text="Two independent click engines · physical hotkeys · coordinate targeting" Foreground="{DynamicResource MutedBrush}" Margin="0,5,0,0"/></StackPanel>\n                                        <Border Grid.Column="1" Style="{StaticResource FluxPill}" VerticalAlignment="Center"><TextBlock Text="TAB READY · 5000+ CPS" FontSize="9" FontWeight="Bold"/></Border>\n                                    </Grid>\n                                </Border>\n                                <Grid>'''
if clicker_anchor not in s:
    raise SystemExit('clicker anchor missing')
s = s.replace(clicker_anchor, clicker_new, 1)
nav_repl = {
    '⌂   Главная': '◈   Dashboard',
    '⚡   Автокликер': '⚡   Auto Engines',
    '↗   Wallhop': '↗   Wallhop Lab',
    '◆   Bolt Actions': '◆   Bolt Actions',
    '◎   Squad Sync': '◎   Squad Sync',
    '⚙   Настройки': '⚙   Appearance',
    '◎   Координаты': '⌖   Coordinates',
    '▦   Профили': '▦   Profiles',
    '≡   Журнал': '≡   Activity',
    '?   Справка': '?   Help',
}
for a,b in nav_repl.items():
    s = s.replace(f'Content="{a}"', f'Content="{b}"')
s = s.replace('PRO 1.0', 'PRO 1.1')
s = s.replace('5.22', '1.1')
save(p, s)

p, s = rw('BrandVisual.cs')
s = s.replace('1.0 · Command Center', '1.1 · Flux UI')
s = s.replace('PRO COMMAND CENTER  •  1.0', 'PRO 1.1  •  FLUX UI')
s = s.replace('PRO 1.0  •  COMMAND CENTER', 'PRO 1.1  •  FLUX UI')
save(p, s)

p, s = rw('RiuClickerCS.csproj')
s = re.sub(r'<Version>[^<]+</Version>', '<Version>1.1.0</Version>', s)
s = re.sub(r'<FileVersion>[^<]+</FileVersion>', '<FileVersion>1.1.0.0</FileVersion>', s)
s = re.sub(r'<AssemblyVersion>[^<]+</AssemblyVersion>', '<AssemblyVersion>1.1.0.0</AssemblyVersion>', s)
save(p, s)

print('Applied RiuClicker Pro 1.1 FLUX UI + TAB hotkey fix')
