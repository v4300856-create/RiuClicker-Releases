from pathlib import Path
import re, shutil
root=Path('src')

def rw(name):
    p=root/name
    return p,p.read_text(encoding='utf-8')
def save(p,s): p.write_text(s,encoding='utf-8')

# Add Pro-only source files without touching the Free build path.
for name in ('MainWindow.Pro.cs','SquadSyncService.cs'):
    shutil.copy2(Path('.build/pro-src')/name, root/name)

# Models / isolated Pro settings.
p,s=rw('Models.cs')
insert='''\npublic sealed class ProMacroActionSettings\n{\n    public bool Enabled { get; set; }\n    public string Hotkey { get; set; } = "";\n    public string SpeedMode { get; set; } = "fast";\n    public string CoordinateId { get; set; } = "";\n}\n\npublic sealed class ProActionsSettings\n{\n    public ProMacroActionSettings BoltPush { get; set; } = new() { Hotkey = "E" };\n    public ProMacroActionSettings Bolts { get; set; } = new() { Hotkey = "V" };\n}\n\npublic sealed class SquadSettings\n{\n    public int Port { get; set; } = 42871;\n    public string DisplayName { get; set; } = "Player";\n}\n'''
if 'public sealed class ProMacroActionSettings' not in s:
    s=s.replace('public sealed class AppearanceSettings',insert+'\npublic sealed class AppearanceSettings')
if 'public ProActionsSettings ProActions' not in s:
    s=s.replace('    public WallhopSettings Wallhop { get; set; } = new();\n', '    public WallhopSettings Wallhop { get; set; } = new();\n    public ProActionsSettings ProActions { get; set; } = new();\n    public SquadSettings Squad { get; set; } = new();\n')
s=s.replace('public const string Name = "Riu Clicker";', 'public const string Name = "RiuClicker Pro";')
s=s.replace('public const string SettingsFolder = "RiuClickerCS";', 'public const string SettingsFolder = "RiuClickerPro";')
if 's.ProActions ??= new();' not in s:
    s=s.replace('        s.Wallhop ??= new();\n', '        s.Wallhop ??= new();\n        s.ProActions ??= new();\n        s.ProActions.BoltPush ??= new() { Hotkey = "E" };\n        s.ProActions.Bolts ??= new() { Hotkey = "V" };\n        s.Squad ??= new();\n        s.Squad.Port = Math.Clamp(s.Squad.Port, 1024, 65535);\n        s.ProActions.BoltPush.SpeedMode = NormalizeProSpeed(s.ProActions.BoltPush.SpeedMode);\n        s.ProActions.Bolts.SpeedMode = NormalizeProSpeed(s.ProActions.Bolts.SpeedMode);\n        if (s.ProActions.BoltPush.Enabled && s.ProActions.Bolts.Enabled) s.ProActions.Bolts.Enabled = false;\n')
if 'private static string NormalizeProSpeed' not in s:
    s=s.replace('    public static ClickerSettings CopyClicker(ClickerSettings s) => new()\n', '    private static string NormalizeProSpeed(string? mode)\n        => mode is "stable" or "fast" or "turbo" or "instant" ? mode : "fast";\n\n    public static ClickerSettings CopyClicker(ClickerSettings s) => new()\n')
save(p,s)

# Input: explicit modifier release for Instant Bolt Push safety.
p,s=rw('InputService.cs')
if 'public static void KeyUp(string name)' not in s:
    target='''    public static void TapKey(string name, int holdMs, CancellationToken token)\n    {\n        if (!TryVirtualKey(name, out var vk)) return;\n        Key(vk, false);\n        if (holdMs > 0 && token.WaitHandle.WaitOne(holdMs)) { Key(vk, true); return; }\n        Key(vk, true);\n    }\n'''
    addition=target+'''\n    public static void KeyDown(string name)\n    {\n        if (TryVirtualKey(name, out var vk)) Key(vk, false);\n    }\n\n    public static void KeyUp(string name)\n    {\n        if (TryVirtualKey(name, out var vk)) Key(vk, true);\n    }\n'''
    if target not in s: raise SystemExit('TapKey target not found')
    s=s.replace(target,addition)
save(p,s)

# Main window: initialize Pro services, route Squad page, safe shutdown, Pro dashboard.
p,s=rw('MainWindow.xaml.cs')
if 'InitializeProFeatures();' not in s:
    s=s.replace('        ApplyBrandLabels();', '        ApplyBrandLabels();\n        InitializeProFeatures();')
if 'PageSquad.Visibility' not in s:
    s=s.replace('        PageMacros.Visibility = page == "Macros" ? Visibility.Visible : Visibility.Collapsed;\n', '        PageMacros.Visibility = page == "Macros" ? Visibility.Visible : Visibility.Collapsed;\n        PageSquad.Visibility = page == "Squad" ? Visibility.Visible : Visibility.Collapsed;\n')
s=s.replace('            "Macros" => (T("МАКРОСЫ"), T("Два макроса могут выполняться одновременно")),', '            "Macros" => ("BOLT ACTIONS", "Built-in Bolt Push and Bolts macros"),\n            "Squad" => ("SQUAD SYNC", "Owner keyboard E/V triggers members’ local assigned actions"),')
if '_squad.StopAsync().GetAwaiter().GetResult();' not in s:
    s=s.replace('    private void Window_Closing(object? sender, CancelEventArgs e)\n    {', '    private void Window_Closing(object? sender, CancelEventArgs e)\n    {\n        _squad.StopAsync().GetAwaiter().GetResult();')
s=re.sub(r'''\n\s*var macroCount = _settings\.Macros\.Count;\n\s*var steps = _settings\.Macros\.Sum\(m => m\.Steps\.Count\);\n\s*HomeMacrosState\.Text = .*?;\n\s*HomeMacrosState\.Foreground = .*?;\n\s*HomeMacrosMeta\.Text = .*?;''', '''\n        var armed = _settings.ProActions.BoltPush.Enabled ? "BOLT PUSH" : _settings.ProActions.Bolts.Enabled ? "BOLTS" : "OFF";\n        HomeMacrosState.Text = armed == "OFF" ? "○ OFF" : "● " + armed;\n        HomeMacrosState.Foreground = armed == "OFF" ? (Brush)FindResource("TextBrush") : (Brush)FindResource("AccentBrush");\n        HomeMacrosMeta.Text = $"Bolt Push · {_settings.ProActions.BoltPush.SpeedMode.ToUpperInvariant()}   |   Bolts · {_settings.ProActions.Bolts.SpeedMode.ToUpperInvariant()}";''', s, count=1, flags=re.S)
if 'Add(_settings.ProActions.BoltPush.Hotkey' not in s:
    s=s.replace('        Add(_settings.Wallhop.Hotkey, "Wallhop");\n', '        Add(_settings.Wallhop.Hotkey, "Wallhop");\n        if (_settings.ProActions.BoltPush.Enabled) Add(_settings.ProActions.BoltPush.Hotkey, "Bolt Push");\n        if (_settings.ProActions.Bolts.Enabled) Add(_settings.ProActions.Bolts.Hotkey, "Bolts");\n')
save(p,s)

# Extras: built-in action hotkeys, owner E/V broadcasting, coordinate refresh, F12 modifier cleanup.
p,s=rw('MainWindow.Extras.cs')
if 'InputService.KeyUp("SHIFT");' not in s:
    s=s.replace('        _macros.StopAll();\n', '        _macros.StopAll();\n        InputService.KeyUp("SHIFT");\n',1)
physical_marker='''        // Only physical hook events reach this method. SendInput from our own\n        // macro/clicker is marked and ignored in InputService.\n'''
if 'var proMatched =' not in s:
    if physical_marker not in s: raise SystemExit('physical hotkey marker not found')
    s=s.replace(physical_marker,physical_marker+'''        if (_squad.IsHost && key is "E" or "V") _ = _squad.BroadcastAsync(key);\n        var proMatched = (_settings.ProActions.BoltPush.Enabled && string.Equals(_settings.ProActions.BoltPush.Hotkey, key, StringComparison.OrdinalIgnoreCase)) ||\n                         (_settings.ProActions.Bolts.Enabled && string.Equals(_settings.ProActions.Bolts.Hotkey, key, StringComparison.OrdinalIgnoreCase));\n        TriggerProHotkey(key, remote: false);\n        if (proMatched) return;\n\n''')
if 'target == "pro_boltpush"' not in s:
    s=s.replace('        else if (target == "wallhop") _settings.Wallhop.Hotkey = key;\n', '        else if (target == "wallhop") _settings.Wallhop.Hotkey = key;\n        else if (target == "pro_boltpush") _settings.ProActions.BoltPush.Hotkey = key;\n        else if (target == "pro_bolts") _settings.ProActions.Bolts.Hotkey = key;\n')
anchor='''        LoadWallhopUi();\n        RefreshCoordinateEditor();\n        RefreshMacroEditor();\n'''
if anchor in s and '        RefreshProUi();\n        Save();' not in s[s.find(anchor):s.find(anchor)+len(anchor)+100]:
    s=s.replace(anchor,anchor+'        RefreshProUi();\n',1)
coord_anchor='''        RefreshCoordinateCombos();\n        RefreshCoordinateEditor();\n'''
if coord_anchor in s:
    s=s.replace(coord_anchor,coord_anchor+'        RefreshProUi();\n',1)
save(p,s)

# Branding is separate from Free and uses its own settings folder.
p,s=rw('BrandVisual.cs')
s=re.sub(r'Title = .*?;', 'Title = $"{BrandInfo.Name} 1.0 · Command Center";', s, count=1)
s=re.sub(r'var name = .*?;', 'var name = "RIUCLICKER PRO";', s, count=1)
s=re.sub(r'HeaderBrandVersionText\.Text = .*?;', 'HeaderBrandVersionText.Text = "PRO COMMAND CENTER  •  1.0";', s, count=1)
s=re.sub(r'SidebarBrandVersionText\.Text = .*?;', 'SidebarBrandVersionText.Text = "PRO 1.0  •  COMMAND CENTER";', s, count=1)
save(p,s)

# Version metadata.
p,s=rw('RiuClickerCS.csproj')
s=re.sub(r'<Version>[^<]+</Version>', '<Version>1.0.0</Version>', s)
s=re.sub(r'<FileVersion>[^<]+</FileVersion>', '<FileVersion>1.0.0.0</FileVersion>', s)
s=re.sub(r'<AssemblyVersion>[^<]+</AssemblyVersion>', '<AssemblyVersion>1.0.0.0</AssemblyVersion>', s)
save(p,s)

# XAML: premium built-in actions and a dedicated Squad Sync page. Legacy macro controls stay collapsed only so old code compiles.
p,s=rw('MainWindow.xaml')
s=s.replace('<Button Content="◆   Макросы" Tag="Macros" Style="{StaticResource NavButton}" Click="Nav_Click"/>', '<Button Content="◆   Bolt Actions" Tag="Macros" Style="{StaticResource NavButton}" Click="Nav_Click"/>\n                            <Button Content="◎   Squad Sync" Tag="Squad" Style="{StaticResource NavButton}" Click="Nav_Click"/>')
s=s.replace('Text="RIU CLICKER"', 'Text="RIUCLICKER PRO"')
s=re.sub(r'Text="5\.2[0-9]  •  NOVA CONTROL"', 'Text="PRO 1.0  •  COMMAND CENTER"', s)
s=s.replace('Text="NOVA CONTROL CENTER"', 'Text="RIUCLICKER PRO · COMMAND CENTER"')
s=s.replace('Content="◆ МАКРОСЫ" Tag="Macros"', 'Content="◆ BOLT ACTIONS" Tag="Macros"')
s=s.replace('Content="ОТКРЫТЬ МАКРОСЫ" Tag="Macros"', 'Content="OPEN BOLT ACTIONS" Tag="Macros"')
start='<Grid x:Name="PageMacros" Visibility="Collapsed">'
end='\n\n                        <!-- WALLHOP PAGE -->'
i=s.find(start); j=s.find(end,i)
if i<0 or j<0: raise SystemExit('PageMacros block not found')
old=s[i:j]
inner=old[len(start):]
k=inner.rfind('</Grid>')
if k<0: raise SystemExit('PageMacros closing grid not found')
inner=inner[:k]+inner[k+len('</Grid>'):]
pro_ui='''<Grid x:Name="PageMacros" Visibility="Collapsed">\n                            <Grid Visibility="Collapsed">'''+inner+'''</Grid>\n                            <ScrollViewer VerticalScrollBarVisibility="Auto">\n                                <StackPanel>\n                                    <Border Style="{StaticResource HeroBorder}" Margin="0,0,0,12"><Grid><Grid.ColumnDefinitions><ColumnDefinition/><ColumnDefinition Width="Auto"/></Grid.ColumnDefinitions><StackPanel><TextBlock Text="BOLT ACTIONS · PRO" FontSize="20" FontWeight="Black" Foreground="{DynamicResource AccentBrush}"/><TextBlock Text="Ready-made combat macros. Bolt Push and Bolts cannot be armed at the same time." Foreground="{DynamicResource MutedBrush}" Margin="0,6,18,0" TextWrapping="Wrap"/></StackPanel><Border Grid.Column="1" Background="#1C0E1720" BorderBrush="{DynamicResource AccentBrush}" BorderThickness="1" CornerRadius="14" Padding="14,8" VerticalAlignment="Center"><TextBlock Text="PRO ACTION ENGINE" FontSize="9" FontWeight="Bold"/></Border></Grid></Border>\n                                    <Grid><Grid.ColumnDefinitions><ColumnDefinition/><ColumnDefinition Width="12"/><ColumnDefinition/></Grid.ColumnDefinitions>\n                                        <Border Grid.Column="0" Style="{StaticResource CardBorder}"><StackPanel><Grid><TextBlock Text="BOLT PUSH" FontSize="17" FontWeight="Black" Foreground="{DynamicResource AccentBrush}"/><TextBlock x:Name="BoltPushState" Text="○ OFF" HorizontalAlignment="Right" FontWeight="Bold"/></Grid><TextBlock Text="Right Click → Shift → V V V → Shift → coordinate click" Foreground="{DynamicResource MutedBrush}" FontSize="10" Margin="0,5,0,12"/><CheckBox x:Name="BoltPushEnabled" Content="ARM BOLT PUSH" Style="{StaticResource RiuCheckBox}" Checked="ProActionToggle_Changed" Unchecked="ProActionToggle_Changed"/><Button x:Name="BoltPushHotkeyButton" Content="HOTKEY · E" Style="{StaticResource RiuButton}" Margin="0,9,0,0" Click="HotkeyCapture_Click" Tag="pro_boltpush"/><TextBlock Text="FINAL COORDINATE" Foreground="{DynamicResource MutedBrush}" FontWeight="Bold" FontSize="9" Margin="0,12,0,5"/><ComboBox x:Name="BoltPushCoordinate" Style="{StaticResource RiuComboBox}" SelectionChanged="BoltPushCoordinate_Changed"/><TextBlock Text="Set the point in Coordinates first. The action shows an error if no valid point is selected." Foreground="{DynamicResource MutedBrush}" FontSize="9" TextWrapping="Wrap" Margin="0,5,0,10"/><TextBlock Text="SPEED" Foreground="{DynamicResource MutedBrush}" FontWeight="Bold" FontSize="9"/><UniformGrid Columns="4" Margin="0,5,0,0"><Button x:Name="BoltPushStable" Content="STABLE" Style="{StaticResource RiuButton}" Margin="2" Click="ProSpeed_Click" Tag="boltpush|stable"/><Button x:Name="BoltPushFast" Content="FAST" Style="{StaticResource RiuButton}" Margin="2" Click="ProSpeed_Click" Tag="boltpush|fast"/><Button x:Name="BoltPushTurbo" Content="TURBO" Style="{StaticResource RiuButton}" Margin="2" Click="ProSpeed_Click" Tag="boltpush|turbo"/><Button x:Name="BoltPushInstant" Content="INSTANT" Style="{StaticResource RiuButton}" Margin="2" Click="ProSpeed_Click" Tag="boltpush|instant"/></UniformGrid><Button Content="▶ TEST BOLT PUSH" Style="{StaticResource AccentButton}" Margin="0,10,0,0" Click="TestProAction_Click" Tag="boltpush"/></StackPanel></Border>\n                                        <Border Grid.Column="2" Style="{StaticResource CardBorder}"><StackPanel><Grid><TextBlock Text="BOLTS" FontSize="17" FontWeight="Black" Foreground="{DynamicResource AccentBrush}"/><TextBlock x:Name="BoltsState" Text="○ OFF" HorizontalAlignment="Right" FontWeight="Bold"/></Grid><TextBlock Text="V V V · lightweight ready-made macro" Foreground="{DynamicResource MutedBrush}" FontSize="10" Margin="0,5,0,12"/><CheckBox x:Name="BoltsEnabled" Content="ARM BOLTS" Style="{StaticResource RiuCheckBox}" Checked="ProActionToggle_Changed" Unchecked="ProActionToggle_Changed"/><Button x:Name="BoltsHotkeyButton" Content="HOTKEY · V" Style="{StaticResource RiuButton}" Margin="0,9,0,0" Click="HotkeyCapture_Click" Tag="pro_bolts"/><TextBlock Text="SPEED" Foreground="{DynamicResource MutedBrush}" FontWeight="Bold" FontSize="9" Margin="0,12,0,0"/><UniformGrid Columns="4" Margin="0,5,0,0"><Button x:Name="BoltsStable" Content="STABLE" Style="{StaticResource RiuButton}" Margin="2" Click="ProSpeed_Click" Tag="bolts|stable"/><Button x:Name="BoltsFast" Content="FAST" Style="{StaticResource RiuButton}" Margin="2" Click="ProSpeed_Click" Tag="bolts|fast"/><Button x:Name="BoltsTurbo" Content="TURBO" Style="{StaticResource RiuButton}" Margin="2" Click="ProSpeed_Click" Tag="bolts|turbo"/><Button x:Name="BoltsInstant" Content="INSTANT" Style="{StaticResource RiuButton}" Margin="2" Click="ProSpeed_Click" Tag="bolts|instant"/></UniformGrid><Border Background="#14251F" BorderBrush="#4F34D399" BorderThickness="1" CornerRadius="12" Padding="12" Margin="0,12,0,0"><TextBlock Text="Arming Bolts automatically disarms Bolt Push, and vice versa." Foreground="{DynamicResource MutedBrush}" TextWrapping="Wrap" FontSize="10"/></Border><Button Content="▶ TEST BOLTS" Style="{StaticResource AccentButton}" Margin="0,10,0,0" Click="TestProAction_Click" Tag="bolts"/></StackPanel></Border>\n                                    </Grid>\n                                    <Border Style="{StaticResource CardBorder}" Margin="0,12,0,0"><StackPanel><TextBlock Text="INSTANT SAFETY" FontWeight="Bold" Foreground="{DynamicResource AccentBrush}"/><TextBlock Text="Instant keeps a tiny mandatory Shift-release safety gap before the final coordinate click so the coordinate click is not lost." Foreground="{DynamicResource MutedBrush}" TextWrapping="Wrap" Margin="0,6,0,0"/></StackPanel></Border>\n                                </StackPanel>\n                            </ScrollViewer>\n                        </Grid>'''
s=s[:i]+pro_ui+s[j:]
squad='''\n\n                        <!-- SQUAD SYNC PAGE -->\n                        <ScrollViewer x:Name="PageSquad" Visibility="Collapsed" VerticalScrollBarVisibility="Auto"><StackPanel>\n                            <Border Style="{StaticResource HeroBorder}" Margin="0,0,0,12"><Grid><Grid.ColumnDefinitions><ColumnDefinition/><ColumnDefinition Width="Auto"/></Grid.ColumnDefinitions><StackPanel><TextBlock Text="SQUAD SYNC" FontSize="20" FontWeight="Black" Foreground="{DynamicResource AccentBrush}"/><TextBlock Text="Owner runs the lobby server on their PC. Physical E/V are the only commands broadcast to connected members." Foreground="{DynamicResource MutedBrush}" TextWrapping="Wrap" Margin="0,6,18,0"/></StackPanel><Border Grid.Column="1" CornerRadius="14" BorderBrush="{DynamicResource AccentBrush}" BorderThickness="1" Padding="14,8" VerticalAlignment="Center"><TextBlock x:Name="SquadRoleText" Text="OFFLINE" FontWeight="Bold"/></Border></Grid></Border>\n                            <Grid><Grid.ColumnDefinitions><ColumnDefinition/><ColumnDefinition Width="12"/><ColumnDefinition/></Grid.ColumnDefinitions><Border Grid.Column="0" Style="{StaticResource CardBorder}"><StackPanel><TextBlock Text="IDENTITY &amp; OWNER SERVER" FontWeight="Bold" Foreground="{DynamicResource AccentBrush}"/><TextBlock Text="Display name" Foreground="{DynamicResource MutedBrush}" Margin="0,9,0,4"/><TextBox x:Name="SquadNameBox" Text="Player" Style="{StaticResource RiuTextBox}"/><TextBlock Text="Owner port" Foreground="{DynamicResource MutedBrush}" Margin="0,9,0,4"/><TextBox x:Name="SquadPortBox" Text="42871" Style="{StaticResource RiuTextBox}"/><Button Content="CREATE SQUAD" Style="{StaticResource AccentButton}" Margin="0,10,0,0" Click="CreateSquad_Click"/><TextBlock Text="Uses UPnP to open the Owner PC. If the router blocks it, the app shows an error instead of silently failing." Foreground="{DynamicResource MutedBrush}" FontSize="9" TextWrapping="Wrap" Margin="0,7,0,0"/></StackPanel></Border><Border Grid.Column="2" Style="{StaticResource CardBorder}"><StackPanel><TextBlock Text="JOIN CODE" FontWeight="Bold" Foreground="{DynamicResource AccentBrush}"/><TextBlock Text="Paste the code from the Owner" Foreground="{DynamicResource MutedBrush}" Margin="0,9,0,4"/><TextBox x:Name="SquadCodeBox" Style="{StaticResource RiuTextBox}" TextWrapping="Wrap"/><Grid Margin="0,9,0,0"><Grid.ColumnDefinitions><ColumnDefinition/><ColumnDefinition/></Grid.ColumnDefinitions><Button Content="JOIN" Style="{StaticResource AccentButton}" Margin="0,0,4,0" Click="JoinSquad_Click"/><Button Grid.Column="1" Content="COPY CODE" Style="{StaticResource RiuButton}" Margin="4,0,0,0" Click="CopySquadCode_Click"/></Grid><Button Content="LEAVE / CLOSE SQUAD" Style="{StaticResource DangerButton}" Margin="0,8,0,0" Click="LeaveSquad_Click"/></StackPanel></Border></Grid>\n                            <Border Style="{StaticResource CardBorder}" Margin="0,12,0,0"><StackPanel><Grid><TextBlock Text="CONNECTION" FontWeight="Bold" Foreground="{DynamicResource AccentBrush}"/><TextBlock x:Name="SquadStatusText" Text="Squad offline" HorizontalAlignment="Right" Foreground="{DynamicResource MutedBrush}"/></Grid><TextBlock x:Name="SquadMembersText" Text="No members" Foreground="{DynamicResource MutedBrush}" Margin="0,8,0,0" TextWrapping="Wrap"/><Border x:Name="SquadOwnerHint" Visibility="Collapsed" Background="#14251F" BorderBrush="#4F34D399" BorderThickness="1" CornerRadius="12" Padding="12" Margin="0,10,0,0"><StackPanel><TextBlock Text="OWNER LIVE SYNC" FontWeight="Bold"/><TextBlock Text="Press physical E or V on the Owner keyboard. Connected members receive only that E/V command and run whichever local Pro action they assigned to the key." Foreground="{DynamicResource MutedBrush}" TextWrapping="Wrap" Margin="0,4,0,0"/></StackPanel></Border></StackPanel></Border>\n                        </StackPanel></ScrollViewer>'''
s=s.replace(end,squad+end)
save(p,s)

print('RiuClicker Pro patch applied')
