from pathlib import Path
import re, shutil

root = Path('src')

def rw(name):
    p = root / name
    return p, p.read_text(encoding='utf-8')

def save(p, s):
    p.write_text(s, encoding='utf-8')

# Add dedicated Bolts engine source.
shutil.copy2(Path('.build/bolts-src/MainWindow.Bolts.cs'), root / 'MainWindow.Bolts.cs')

# Settings model: two independent built-in bolt actions with four speed modes.
p, s = rw('Models.cs')
insert = '''\npublic sealed class BoltMacroSettings\n{\n    public bool Enabled { get; set; }\n    public string Hotkey { get; set; } = "";\n    public string SpeedMode { get; set; } = "fast";\n    public string CoordinateId { get; set; } = "";\n}\n\npublic sealed class BoltsSettings\n{\n    public BoltMacroSettings BoltPush { get; set; } = new() { Hotkey = "E" };\n    public BoltMacroSettings Bolts { get; set; } = new() { Hotkey = "V" };\n}\n'''
if 'public sealed class BoltMacroSettings' not in s:
    s = s.replace('public sealed class AppearanceSettings', insert + '\npublic sealed class AppearanceSettings')
if 'public BoltsSettings Bolts' not in s:
    s = s.replace('    public WallhopSettings Wallhop { get; set; } = new();\n', '    public WallhopSettings Wallhop { get; set; } = new();\n    public BoltsSettings Bolts { get; set; } = new();\n')
if 's.Bolts ??= new();' not in s:
    s = s.replace('        s.Wallhop ??= new();\n', '        s.Wallhop ??= new();\n        s.Bolts ??= new();\n        s.Bolts.BoltPush ??= new() { Hotkey = "E" };\n        s.Bolts.Bolts ??= new() { Hotkey = "V" };\n        s.Bolts.BoltPush.SpeedMode = NormalizeBoltSpeed(s.Bolts.BoltPush.SpeedMode);\n        s.Bolts.Bolts.SpeedMode = NormalizeBoltSpeed(s.Bolts.Bolts.SpeedMode);\n')
if 'private static string NormalizeBoltSpeed' not in s:
    s = s.replace('    public static ClickerSettings CopyClicker(ClickerSettings s) => new()\n', '    private static string NormalizeBoltSpeed(string? mode)\n        => mode is "stable" or "fast" or "turbo" or "instant" ? mode : "fast";\n\n    public static ClickerSettings CopyClicker(ClickerSettings s) => new()\n')
save(p, s)

# Input helpers used by the non-blocking action engine.
p, s = rw('InputService.cs')
if 'public static void KeyUp(string name)' not in s:
    target = '''    public static void TapKey(string name, int holdMs, CancellationToken token)\n    {\n        if (!TryVirtualKey(name, out var vk)) return;\n        Key(vk, false);\n        if (holdMs > 0 && token.WaitHandle.WaitOne(holdMs)) { Key(vk, true); return; }\n        Key(vk, true);\n    }\n'''
    addition = target + '''\n    public static void KeyDown(string name)\n    {\n        if (TryVirtualKey(name, out var vk)) Key(vk, false);\n    }\n\n    public static void KeyUp(string name)\n    {\n        if (TryVirtualKey(name, out var vk)) Key(vk, true);\n    }\n'''
    if target not in s:
        raise SystemExit('TapKey target not found')
    s = s.replace(target, addition)
save(p, s)

# Initialize the new tab and show friendly page title.
p, s = rw('MainWindow.xaml.cs')
if 'InitializeBoltsFeatures();' not in s:
    s = s.replace('        ApplyBrandLabels();', '        ApplyBrandLabels();\n        InitializeBoltsFeatures();')
s = s.replace('            "Macros" => (T("МАКРОСЫ"), T("Два макроса могут выполняться одновременно")),', '            "Macros" => ("BOLTS", "Bolt Push and Bolts · independent speed modes"),')
# Dashboard wording if present.
s = s.replace('Content="◆ МАКРОСЫ" Tag="Macros"', 'Content="◆ BOLTS" Tag="Macros"')
save(p, s)

# Route physical hotkeys and hotkey capture to built-in Bolts actions.
p, s = rw('MainWindow.Extras.cs')
physical_marker = '''        // Only physical hook events reach this method. SendInput from our own\n        // macro/clicker is marked and ignored in InputService.\n'''
if 'var boltMatched =' not in s:
    if physical_marker not in s:
        raise SystemExit('physical hotkey marker not found')
    s = s.replace(physical_marker, physical_marker + '''        var boltMatched = (_settings.Bolts.BoltPush.Enabled && string.Equals(_settings.Bolts.BoltPush.Hotkey, key, StringComparison.OrdinalIgnoreCase)) ||\n                          (_settings.Bolts.Bolts.Enabled && string.Equals(_settings.Bolts.Bolts.Hotkey, key, StringComparison.OrdinalIgnoreCase));\n        TriggerBoltHotkey(key);\n        if (boltMatched) return;\n\n''')
if 'target == "boltpush"' not in s:
    s = s.replace('        else if (target == "wallhop") _settings.Wallhop.Hotkey = key;\n', '        else if (target == "wallhop") _settings.Wallhop.Hotkey = key;\n        else if (target == "boltpush") _settings.Bolts.BoltPush.Hotkey = key;\n        else if (target == "bolts") _settings.Bolts.Bolts.Hotkey = key;\n')
# Keep modifier state clean on emergency stop.
if 'InputService.KeyUp("SHIFT");' not in s:
    s = s.replace('        _macros.StopAll();\n', '        _macros.StopAll();\n        InputService.KeyUp("V");\n        InputService.KeyUp("SHIFT");\n', 1)
# Refresh coordinates in Bolts selector after coordinate changes/load.
coord_anchor = '''        RefreshCoordinateCombos();\n        RefreshCoordinateEditor();\n'''
if coord_anchor in s and 'RefreshBoltsUi();' not in s[s.find(coord_anchor):s.find(coord_anchor)+len(coord_anchor)+80]:
    s = s.replace(coord_anchor, coord_anchor + '        RefreshBoltsUi();\n', 1)
save(p, s)

# XAML: keep legacy macro controls hidden so old code still compiles, but replace visible page with Bolts.
p, s = rw('MainWindow.xaml')
s = s.replace('<Button Content="◆   Макросы" Tag="Macros" Style="{StaticResource NavButton}" Click="Nav_Click"/>', '<Button Content="◆   Bolts" Tag="Macros" Style="{StaticResource NavButton}" Click="Nav_Click"/>')
s = s.replace('Content="◆ МАКРОСЫ" Tag="Macros"', 'Content="◆ BOLTS" Tag="Macros"')
s = s.replace('Content="ОТКРЫТЬ МАКРОСЫ" Tag="Macros"', 'Content="OPEN BOLTS" Tag="Macros"')
start = '<Grid x:Name="PageMacros" Visibility="Collapsed">'
end = '\n\n                        <!-- WALLHOP PAGE -->'
i = s.find(start)
j = s.find(end, i)
if i < 0 or j < 0:
    raise SystemExit('PageMacros block not found')
old = s[i:j]
inner = old[len(start):]
k = inner.rfind('</Grid>')
if k < 0:
    raise SystemExit('PageMacros closing grid not found')
inner = inner[:k] + inner[k+len('</Grid>'):]

bolts_ui = '''<Grid x:Name="PageMacros" Visibility="Collapsed">\n                            <Grid Visibility="Collapsed">''' + inner + '''</Grid>\n                            <ScrollViewer VerticalScrollBarVisibility="Auto">\n                                <StackPanel>\n                                    <Border Style="{StaticResource HeroBorder}" Margin="0,0,0,12">\n                                        <StackPanel>\n                                            <TextBlock Text="BOLTS" FontSize="22" FontWeight="Black" Foreground="{DynamicResource AccentBrush}"/>\n                                            <TextBlock Text="Two built-in macros with independent hotkeys and speed modes. Async timing keeps the UI responsive." Foreground="{DynamicResource MutedBrush}" Margin="0,6,0,0" TextWrapping="Wrap"/>\n                                        </StackPanel>\n                                    </Border>\n                                    <Grid>\n                                        <Grid.ColumnDefinitions><ColumnDefinition/><ColumnDefinition Width="12"/><ColumnDefinition/></Grid.ColumnDefinitions>\n                                        <Border Grid.Column="0" Style="{StaticResource CardBorder}">\n                                            <StackPanel>\n                                                <Grid><TextBlock Text="BOLT PUSH" FontSize="17" FontWeight="Black" Foreground="{DynamicResource AccentBrush}"/><TextBlock x:Name="BoltPushState" Text="○ OFF" HorizontalAlignment="Right" FontWeight="Bold"/></Grid>\n                                                <TextBlock Text="Shift → V V V → Shift → saved-coordinate click" Foreground="{DynamicResource MutedBrush}" FontSize="10" Margin="0,5,0,12"/>\n                                                <CheckBox x:Name="BoltPushEnabled" Content="ENABLE BOLT PUSH" Style="{StaticResource RiuCheckBox}" Checked="BoltActionToggle_Changed" Unchecked="BoltActionToggle_Changed"/>\n                                                <Button x:Name="BoltPushHotkeyButton" Content="HOTKEY · E" Style="{StaticResource RiuButton}" Margin="0,9,0,0" Click="HotkeyCapture_Click" Tag="boltpush"/>\n                                                <TextBlock Text="FINAL COORDINATE" Foreground="{DynamicResource MutedBrush}" FontWeight="Bold" FontSize="9" Margin="0,12,0,5"/>\n                                                <ComboBox x:Name="BoltPushCoordinate" Style="{StaticResource RiuComboBox}" SelectionChanged="BoltPushCoordinate_Changed"/>\n                                                <TextBlock Text="SPEED" Foreground="{DynamicResource MutedBrush}" FontWeight="Bold" FontSize="9" Margin="0,12,0,4"/>\n                                                <UniformGrid Columns="4">\n                                                    <Button x:Name="BoltPushStable" Content="STABLE" Style="{StaticResource RiuButton}" Margin="2" Click="BoltSpeed_Click" Tag="boltpush|stable"/>\n                                                    <Button x:Name="BoltPushFast" Content="FAST" Style="{StaticResource RiuButton}" Margin="2" Click="BoltSpeed_Click" Tag="boltpush|fast"/>\n                                                    <Button x:Name="BoltPushTurbo" Content="TURBO" Style="{StaticResource RiuButton}" Margin="2" Click="BoltSpeed_Click" Tag="boltpush|turbo"/>\n                                                    <Button x:Name="BoltPushInstant" Content="INSTANT" Style="{StaticResource RiuButton}" Margin="2" Click="BoltSpeed_Click" Tag="boltpush|instant"/>\n                                                </UniformGrid>\n                                                <Button Content="▶ TEST BOLT PUSH" Style="{StaticResource AccentButton}" Margin="0,10,0,0" Click="TestBoltAction_Click" Tag="boltpush"/>\n                                            </StackPanel>\n                                        </Border>\n                                        <Border Grid.Column="2" Style="{StaticResource CardBorder}">\n                                            <StackPanel>\n                                                <Grid><TextBlock Text="BOLTS" FontSize="17" FontWeight="Black" Foreground="{DynamicResource AccentBrush}"/><TextBlock x:Name="BoltsState" Text="○ OFF" HorizontalAlignment="Right" FontWeight="Bold"/></Grid>\n                                                <TextBlock Text="V → V → V" Foreground="{DynamicResource MutedBrush}" FontSize="10" Margin="0,5,0,12"/>\n                                                <CheckBox x:Name="BoltsEnabled" Content="ENABLE BOLTS" Style="{StaticResource RiuCheckBox}" Checked="BoltActionToggle_Changed" Unchecked="BoltActionToggle_Changed"/>\n                                                <Button x:Name="BoltsHotkeyButton" Content="HOTKEY · V" Style="{StaticResource RiuButton}" Margin="0,9,0,0" Click="HotkeyCapture_Click" Tag="bolts"/>\n                                                <TextBlock Text="SPEED" Foreground="{DynamicResource MutedBrush}" FontWeight="Bold" FontSize="9" Margin="0,12,0,4"/>\n                                                <UniformGrid Columns="4">\n                                                    <Button x:Name="BoltsStable" Content="STABLE" Style="{StaticResource RiuButton}" Margin="2" Click="BoltSpeed_Click" Tag="bolts|stable"/>\n                                                    <Button x:Name="BoltsFast" Content="FAST" Style="{StaticResource RiuButton}" Margin="2" Click="BoltSpeed_Click" Tag="bolts|fast"/>\n                                                    <Button x:Name="BoltsTurbo" Content="TURBO" Style="{StaticResource RiuButton}" Margin="2" Click="BoltSpeed_Click" Tag="bolts|turbo"/>\n                                                    <Button x:Name="BoltsInstant" Content="INSTANT" Style="{StaticResource RiuButton}" Margin="2" Click="BoltSpeed_Click" Tag="bolts|instant"/>\n                                                </UniformGrid>\n                                                <Button Content="▶ TEST BOLTS" Style="{StaticResource AccentButton}" Margin="0,10,0,0" Click="TestBoltAction_Click" Tag="bolts"/>\n                                            </StackPanel>\n                                        </Border>\n                                    </Grid>\n                                </StackPanel>\n                            </ScrollViewer>\n                        </Grid>'''
s = s[:i] + bolts_ui + s[j:]

# Version visible and metadata become 5.23 while preserving 5.22 design.
s = s.replace('5.22', '5.23')
save(p, s)

# Brand/version-bearing code and project metadata.
for name in ('MainWindow.xaml.cs', 'MainWindow.Extras.cs', 'BrandVisual.cs', 'Models.cs'):
    p, t = rw(name)
    t = t.replace('5.22', '5.23')
    save(p, t)

p, s = rw('RiuClickerCS.csproj')
s = re.sub(r'<Version>[^<]+</Version>', '<Version>5.23.0</Version>', s)
s = re.sub(r'<FileVersion>[^<]+</FileVersion>', '<FileVersion>5.23.0.0</FileVersion>', s)
s = re.sub(r'<AssemblyVersion>[^<]+</AssemblyVersion>', '<AssemblyVersion>5.23.0.0</AssemblyVersion>', s)
save(p, s)

print('Applied RiuClicker 5.23 Bolts tab patch')
