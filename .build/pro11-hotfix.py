from pathlib import Path
import re

root = Path('src')

def rw(name):
    p = root / name
    return p, p.read_text(encoding='utf-8')

def save(p, s):
    p.write_text(s, encoding='utf-8')

# Main window: TAB capture fix + Prism shell refresh.
p, s = rw('MainWindow.xaml')
if 'PreviewKeyDown="Window_PreviewKeyDown"' not in s:
    s = s.replace('Background="{DynamicResource WindowBrush}" Loaded="Window_Loaded" Closing="Window_Closing">',
                  'Background="{DynamicResource WindowBrush}" Loaded="Window_Loaded" Closing="Window_Closing" PreviewKeyDown="Window_PreviewKeyDown" UseLayoutRounding="True" SnapsToDevicePixels="True">')
s = s.replace('Title="Riu Clicker 5.22 · Nova Control" Width="1180" Height="790" MinWidth="1000" MinHeight="660"',
              'Title="RiuClicker Pro 1.1 · Prism Command" Width="1260" Height="840" MinWidth="1080" MinHeight="700"')
s = s.replace('<Grid.RowDefinitions><RowDefinition Height="50"/><RowDefinition Height="*"/></Grid.RowDefinitions>', '<Grid.RowDefinitions><RowDefinition Height="58"/><RowDefinition Height="*"/></Grid.RowDefinitions>', 1)
s = s.replace('<Grid.ColumnDefinitions><ColumnDefinition Width="232"/><ColumnDefinition Width="*"/></Grid.ColumnDefinitions>', '<Grid.ColumnDefinitions><ColumnDefinition Width="252"/><ColumnDefinition Width="*"/></Grid.ColumnDefinitions>', 1)
s = s.replace('<Grid Grid.Column="1" Margin="24,18,24,20">', '<Grid Grid.Column="1" Margin="30,22,30,26">', 1)
s = s.replace('Margin="2,0,2,16"', 'Margin="2,0,2,20"', 1)
s = s.replace('Text="ГЛАВНАЯ" FontSize="29" FontWeight="Black"', 'Text="ГЛАВНАЯ" FontSize="32" FontWeight="Black"')
s = s.replace('Text="PHYSICAL HOTKEYS"', 'Text="PRO 1.1 · INPUT CORE"')
s = s.replace('Text="RIUCLICKER PRO · COMMAND CENTER"', 'Text="RIUCLICKER PRO · PRISM COMMAND"')
s = s.replace('Text="PRO 1.0  •  COMMAND CENTER"', 'Text="PRO 1.1  •  PRISM COMMAND"')
s = s.replace('Text="NOVA CONTROL  •  5.22"', 'Text="PRISM COMMAND  •  1.1"')
s = s.replace('Text="3D · LIVE"', 'Text="PRISM · LIVE"')
s = s.replace('Content="⌂   Главная"', 'Content="◈   Dashboard"')
s = s.replace('Content="⚡   Автокликер"', 'Content="ϟ   Auto Clicker"')
s = s.replace('Content="⚙   Настройки"', 'Content="⚙   Settings"')
s = s.replace('Content="◎   Координаты"', 'Content="⌖   Coordinates"')
s = s.replace('Content="▦   Профили"', 'Content="▦   Profiles"')
s = s.replace('Content="≡   Журнал"', 'Content="≡   Activity"')
s = s.replace('Content="?   Справка"', 'Content="?   Help"')
s = s.replace('Text="ОСНОВНОЕ"', 'Text="COMMAND"').replace('Text="ИНСТРУМЕНТЫ"', 'Text="TOOLS"').replace('Text="СИСТЕМА"', 'Text="SYSTEM CORE"')
s = s.replace('Content="F12 · ОСТАНОВИТЬ ВСЁ"', 'Content="F12 · KILL SWITCH"')
s = s.replace('x:Name="HomeC1Meta" Text="F8 · 12 CPS · ЛКМ"', 'x:Name="HomeC1Meta" Text="Loading hotkey…"')
s = s.replace('x:Name="C1HotkeyButton" Content="ЗАПУСК · F8"', 'x:Name="C1HotkeyButton" Content="ЗАПУСК · —"')
s = s.replace('x:Name="C2HotkeyButton" Content="ЗАПУСК · F9"', 'x:Name="C2HotkeyButton" Content="ЗАПУСК · —"')
old_help = '<TextBlock Text="F8 — кликер 1   ·   F9 — кликер 2   ·   F7 — поворот камеры   ·   F12 — остановить всё" Foreground="{DynamicResource MutedBrush}" Margin="0,5,0,10" TextWrapping="Wrap"/>'
if old_help in s:
    s = s.replace(old_help, '<TextBlock x:Name="HelpHotkeysText" Text="Current hotkeys will appear here" Foreground="{DynamicResource MutedBrush}" Margin="0,5,0,10" TextWrapping="Wrap"/>', 1)
# Two Prism ambient glows instead of the old single cyan blob.
old_glow = '''        <Ellipse Width="640" Height="640" HorizontalAlignment="Right" VerticalAlignment="Top" Margin="0,-360,-260,0"
                 IsHitTestVisible="False" Opacity=".75">
            <Ellipse.Fill>
                <RadialGradientBrush>
                    <GradientStop Color="#3522D3EE" Offset="0"/>
                    <GradientStop Color="#1022D3EE" Offset=".38"/>
                    <GradientStop Color="#00070A10" Offset="1"/>
                </RadialGradientBrush>
            </Ellipse.Fill>
        </Ellipse>'''
new_glow = '''        <Ellipse Width="760" Height="760" HorizontalAlignment="Right" VerticalAlignment="Top" Margin="0,-430,-270,0" IsHitTestVisible="False" Opacity=".72">
            <Ellipse.Fill><RadialGradientBrush><GradientStop Color="#507C3AED" Offset="0"/><GradientStop Color="#1A7C3AED" Offset=".36"/><GradientStop Color="#0005070B" Offset="1"/></RadialGradientBrush></Ellipse.Fill>
        </Ellipse>
        <Ellipse Width="620" Height="620" HorizontalAlignment="Left" VerticalAlignment="Bottom" Margin="-360,0,0,-390" IsHitTestVisible="False" Opacity=".52">
            <Ellipse.Fill><RadialGradientBrush><GradientStop Color="#3522D3EE" Offset="0"/><GradientStop Color="#1022D3EE" Offset=".4"/><GradientStop Color="#0005070B" Offset="1"/></RadialGradientBrush></Ellipse.Fill>
        </Ellipse>'''
if old_glow in s:
    s = s.replace(old_glow, new_glow, 1)
save(p, s)

# WPF normally steals TAB for focus navigation. In hotkey-capture mode we swallow that navigation;
# the existing physical hook then stores TAB exactly like any F-key/mouse key.
p, s = rw('MainWindow.xaml.cs')
if 'private void Window_PreviewKeyDown' not in s:
    marker = '    private void Window_Closing(object? sender, CancelEventArgs e)\n'
    handler = '''    private void Window_PreviewKeyDown(object sender, KeyEventArgs e)
    {
        if (_captureTarget is not null && (e.Key == Key.Tab || e.SystemKey == Key.Tab))
            e.Handled = true;
    }

'''
    if marker not in s: raise SystemExit('Window closing marker missing')
    s = s.replace(marker, handler + marker, 1)
if 'foreach (var item in NavPanel.Children.OfType<Button>())' not in s:
    marker = '        _currentPage = page;\n'
    nav = '''        _currentPage = page;
        if (NavPanel is not null)
        {
            foreach (var item in NavPanel.Children.OfType<Button>())
            {
                var active = string.Equals(item.Tag?.ToString(), page, StringComparison.OrdinalIgnoreCase);
                item.Background = active ? (Brush)FindResource("AccentSoftBrush") : Brushes.Transparent;
                item.BorderBrush = active ? (Brush)FindResource("AccentBrush") : Brushes.Transparent;
                item.Foreground = active ? (Brush)FindResource("TextBrush") : (Brush)FindResource("MutedBrush");
                item.FontWeight = active ? FontWeights.Bold : FontWeights.SemiBold;
            }
        }
'''
    if marker not in s: raise SystemExit('ShowPage marker missing')
    s = s.replace(marker, nav, 1)
needle = '        HomeC2Meta.Text = $"{c2.Hotkey} · {c2.Cps:0.#} CPS · {MouseDisplay(c2.MouseButton)} · {(c2.Activation == "hold" ? "HOLD" : "TOGGLE")}";\n'
if 'HelpHotkeysText.Text' not in s:
    if needle not in s: raise SystemExit('Dashboard marker missing')
    s = s.replace(needle, needle + '        if (HelpHotkeysText is not null) HelpHotkeysText.Text = $"Clicker 1 · {c1.Hotkey}   |   Clicker 2 · {c2.Hotkey}   |   Wallhop · {_settings.Wallhop.Hotkey}   |   F12 · KILL SWITCH";\n', 1)
save(p, s)

# Pro hotkeys participate in conflict checks too.
p, s = rw('MainWindow.Extras.cs')
section_a = s.find('private bool CanAssignHotkey')
section_b = s.find('// ---------------- Coordinates', section_a)
section = s[section_a:section_b]
if 'Bolt Push", target == "pro_boltpush"' not in section:
    marker = '        Check(_settings.Wallhop.Hotkey, "Wallhop", target == "wallhop");\n'
    if marker not in s: raise SystemExit('Conflict marker missing')
    s = s.replace(marker, marker + '        Check(_settings.ProActions.BoltPush.Hotkey, "Bolt Push", target == "pro_boltpush");\n        Check(_settings.ProActions.Bolts.Hotkey, "Bolts", target == "pro_bolts");\n', 1)
save(p, s)

# Global Prism design system: violet/cyan glass, larger radii, premium cards.
p, s = rw('App.xaml')
s = s.replace('RIU 5.22 · NOVA CONTROL UI', 'RIU PRO 1.1 · PRISM COMMAND UI')
for a,b in {
    '#22D3EE':'#8B5CF6','#2422D3EE':'#2F8B5CF6','#070A10':'#05070B','#090D14':'#080B12',
    '#101620':'#0D121D','#161E2A':'#151C2A','#0B111A':'#0A0F19','#121B28':'#141B29',
    '#253142':'#2B3550','#182230':'#1B2436','#F3F7FC':'#F7F7FB','#8795A8':'#8F9AAF',
    '#FF526D':'#FF5C7A','#44E2A1':'#3DE0B2','#151D28':'#111827','#34465A':'#37445F'
}.items(): s = s.replace(a,b)
anchor = '<SolidColorBrush x:Key="AccentSoftBrush" Color="#2F8B5CF6"/>'
if 'x:Key="Accent2Brush"' not in s:
    if anchor not in s: raise SystemExit('Accent anchor missing')
    s = s.replace(anchor, anchor + '\n        <SolidColorBrush x:Key="Accent2Brush" Color="#22D3EE"/>\n        <SolidColorBrush x:Key="GlassBrush" Color="#B30D121D"/>\n        <SolidColorBrush x:Key="GlassStrongBrush" Color="#E30A0F19"/>', 1)
s = s.replace('<Setter Property="Padding" Value="14,10"/>', '<Setter Property="Padding" Value="16,11"/>', 1)
s = s.replace('<Border x:Name="Glow" CornerRadius="12"', '<Border x:Name="Glow" CornerRadius="15"', 1)
s = s.replace('CornerRadius="11"\n                                    Background="{TemplateBinding Background}"', 'CornerRadius="14"\n                                    Background="{TemplateBinding Background}"', 1)
s = s.replace('CornerRadius="10" Height="1"', 'CornerRadius="13" Height="1"', 1)
s = s.replace('<Setter Property="Height" Value="46"/>', '<Setter Property="Height" Value="48"/>', 1)
s = s.replace('<Setter Property="Padding" Value="15,0"/>', '<Setter Property="Padding" Value="16,0"/>', 1)
s = s.replace('<Setter Property="Margin" Value="0,3"/>', '<Setter Property="Margin" Value="0,4"/>', 1)
old_card = '''        <Style TargetType="Border" x:Key="CardBorder">
            <Setter Property="Background" Value="{DynamicResource CardBrush}"/>
            <Setter Property="BorderBrush" Value="{DynamicResource LineSoftBrush}"/>
            <Setter Property="BorderThickness" Value="1"/>
            <Setter Property="CornerRadius" Value="16"/>
            <Setter Property="Padding" Value="18"/>
        </Style>'''
new_card = '''        <Style TargetType="Border" x:Key="CardBorder">
            <Setter Property="Background" Value="{DynamicResource GlassBrush}"/>
            <Setter Property="BorderBrush" Value="{DynamicResource LineBrush}"/>
            <Setter Property="BorderThickness" Value="1"/>
            <Setter Property="CornerRadius" Value="20"/>
            <Setter Property="Padding" Value="20"/>
        </Style>'''
if old_card in s: s = s.replace(old_card,new_card,1)
old_hero = '''        <Style TargetType="Border" x:Key="HeroBorder" BasedOn="{StaticResource CardBorder}">
            <Setter Property="Background" Value="#111827"/>
            <Setter Property="BorderBrush" Value="#37445F"/>
            <Setter Property="Padding" Value="20"/>
        </Style>'''
new_hero = '''        <Style TargetType="Border" x:Key="HeroBorder" BasedOn="{StaticResource CardBorder}">
            <Setter Property="BorderBrush" Value="#5B6B8A"/>
            <Setter Property="Padding" Value="22"/>
            <Setter Property="Background"><Setter.Value><LinearGradientBrush StartPoint="0,0" EndPoint="1,1"><GradientStop Color="#E3121724" Offset="0"/><GradientStop Color="#B3231740" Offset="0.58"/><GradientStop Color="#A20C2030" Offset="1"/></LinearGradientBrush></Setter.Value></Setter>
        </Style>'''
if old_hero in s: s = s.replace(old_hero,new_hero,1)
save(p,s)

# Version/branding.
p,s = rw('BrandVisual.cs')
s = re.sub(r'Title = \$"\{BrandInfo\.Name\} 1\.0 · Command Center";', 'Title = $"{BrandInfo.Name} 1.1 · Prism Command";', s)
s = s.replace('HeaderBrandVersionText.Text = "PRO COMMAND CENTER  •  1.0";', 'HeaderBrandVersionText.Text = "PRISM COMMAND  •  1.1";')
s = s.replace('SidebarBrandVersionText.Text = "PRO 1.0  •  COMMAND CENTER";', 'SidebarBrandVersionText.Text = "PRO 1.1  •  PRISM COMMAND";')
save(p,s)
p,s = rw('RiuClickerCS.csproj')
s = re.sub(r'<Version>[^<]+</Version>', '<Version>1.1.0</Version>', s)
s = re.sub(r'<FileVersion>[^<]+</FileVersion>', '<FileVersion>1.1.0.0</FileVersion>', s)
s = re.sub(r'<AssemblyVersion>[^<]+</AssemblyVersion>', '<AssemblyVersion>1.1.0.0</AssemblyVersion>', s)
save(p,s)
for name in ('MainWindow.xaml','MainWindow.xaml.cs','MainWindow.Extras.cs','MainWindow.Pro.cs'):
    p,s = rw(name); save(p,s.replace('PRO 1.0','PRO 1.1').replace('Pro 1.0','Pro 1.1'))

print('Applied RiuClicker Pro 1.1 Prism UI + TAB hotkey fix')
