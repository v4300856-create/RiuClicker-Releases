from pathlib import Path

root = Path('src')

def rw(name):
    p = root / name
    return p, p.read_text(encoding='utf-8')

def save(p, s):
    p.write_text(s, encoding='utf-8')

# --- Settings model ---
p, s = rw('Models.cs')
if 'public BoltMacroSettings ClickVClick' not in s:
    s = s.replace(
        '    public BoltMacroSettings Bolts { get; set; } = new() { Hotkey = "V" };\n',
        '    public BoltMacroSettings Bolts { get; set; } = new() { Hotkey = "V" };\n    public BoltMacroSettings ClickVClick { get; set; } = new() { Hotkey = "C" };\n'
    )
if 's.Bolts.ClickVClick ??=' not in s:
    s = s.replace(
        '        s.Bolts.Bolts ??= new() { Hotkey = "V" };\n',
        '        s.Bolts.Bolts ??= new() { Hotkey = "V" };\n        s.Bolts.ClickVClick ??= new() { Hotkey = "C" };\n'
    )
if 's.Bolts.ClickVClick.SpeedMode' not in s:
    s = s.replace(
        '        s.Bolts.Bolts.SpeedMode = NormalizeBoltSpeed(s.Bolts.Bolts.SpeedMode);\n',
        '        s.Bolts.Bolts.SpeedMode = NormalizeBoltSpeed(s.Bolts.Bolts.SpeedMode);\n        s.Bolts.ClickVClick.SpeedMode = NormalizeBoltSpeed(s.Bolts.ClickVClick.SpeedMode);\n'
    )
save(p, s)

# --- Physical hotkeys + hotkey capture ---
p, s = rw('MainWindow.Extras.cs')
old = '''        var boltMatched = (_settings.Bolts.BoltPush.Enabled && string.Equals(_settings.Bolts.BoltPush.Hotkey, key, StringComparison.OrdinalIgnoreCase)) ||\n                          (_settings.Bolts.Bolts.Enabled && string.Equals(_settings.Bolts.Bolts.Hotkey, key, StringComparison.OrdinalIgnoreCase));'''
new = '''        var boltMatched = (_settings.Bolts.BoltPush.Enabled && string.Equals(_settings.Bolts.BoltPush.Hotkey, key, StringComparison.OrdinalIgnoreCase)) ||\n                          (_settings.Bolts.Bolts.Enabled && string.Equals(_settings.Bolts.Bolts.Hotkey, key, StringComparison.OrdinalIgnoreCase)) ||\n                          (_settings.Bolts.ClickVClick.Enabled && string.Equals(_settings.Bolts.ClickVClick.Hotkey, key, StringComparison.OrdinalIgnoreCase));'''
if old in s:
    s = s.replace(old, new)
if 'target == "clickvclick"' not in s:
    s = s.replace(
        '        else if (target == "bolts") _settings.Bolts.Bolts.Hotkey = key;\n',
        '        else if (target == "bolts") _settings.Bolts.Bolts.Hotkey = key;\n        else if (target == "clickvclick") _settings.Bolts.ClickVClick.Hotkey = key;\n'
    )
save(p, s)

# --- Engine ---
p, s = rw('MainWindow.Bolts.cs')
if '_clickVClickRun' not in s:
    s = s.replace(
        '    private readonly SemaphoreSlim _boltsRun = new(1, 1);\n',
        '    private readonly SemaphoreSlim _boltsRun = new(1, 1);\n    private readonly SemaphoreSlim _clickVClickRun = new(1, 1);\n'
    )
if 'var c = _settings.Bolts.ClickVClick;' not in s:
    s = s.replace(
        '        var b = _settings.Bolts.Bolts;\n',
        '        var b = _settings.Bolts.Bolts;\n        var c = _settings.Bolts.ClickVClick;\n', 1
    )
if 'ClickVClickEnabled.IsChecked' not in s:
    s = s.replace(
        '        BoltsEnabled.IsChecked = b.Enabled;\n',
        '        BoltsEnabled.IsChecked = b.Enabled;\n        ClickVClickEnabled.IsChecked = c.Enabled;\n'
    )
    s = s.replace(
        '        BoltsHotkeyButton.Content = $"HOTKEY · {(string.IsNullOrWhiteSpace(b.Hotkey) ? "NONE" : b.Hotkey)}";\n',
        '        BoltsHotkeyButton.Content = $"HOTKEY · {(string.IsNullOrWhiteSpace(b.Hotkey) ? "NONE" : b.Hotkey)}";\n        ClickVClickHotkeyButton.Content = $"HOTKEY · {(string.IsNullOrWhiteSpace(c.Hotkey) ? "NONE" : c.Hotkey)}";\n'
    )
if 'ClickVClickCoordinate.ItemsSource' not in s:
    anchor = '''        BoltPushCoordinate.SelectedItem = _settings.Coordinates.FirstOrDefault(c => c.Id == p.CoordinateId) ?? selected;\n'''
    add = anchor + '''\n        var selectedClick = ClickVClickCoordinate.SelectedItem as CoordinateItem;\n        ClickVClickCoordinate.ItemsSource = null;\n        ClickVClickCoordinate.ItemsSource = _settings.Coordinates;\n        ClickVClickCoordinate.DisplayMemberPath = nameof(CoordinateItem.Display);\n        ClickVClickCoordinate.SelectedItem = _settings.Coordinates.FirstOrDefault(x => x.Id == c.CoordinateId) ?? selectedClick;\n'''
    s = s.replace(anchor, add)
if 'PaintBoltSpeedButtons("clickvclick"' not in s:
    s = s.replace(
        '        PaintBoltSpeedButtons("bolts", b.SpeedMode);\n',
        '        PaintBoltSpeedButtons("bolts", b.SpeedMode);\n        PaintBoltSpeedButtons("clickvclick", c.SpeedMode);\n'
    )
if 'ClickVClickState.Text' not in s:
    s = s.replace(
        '        BoltsState.Text = b.Enabled ? "● ARMED" : "○ OFF";\n',
        '        BoltsState.Text = b.Enabled ? "● ARMED" : "○ OFF";\n        ClickVClickState.Text = c.Enabled ? "● ARMED" : "○ OFF";\n'
    )
    s = s.replace(
        '        BoltsState.Foreground = b.Enabled ? (Brush)FindResource("SuccessBrush") : (Brush)FindResource("MutedBrush");\n',
        '        BoltsState.Foreground = b.Enabled ? (Brush)FindResource("SuccessBrush") : (Brush)FindResource("MutedBrush");\n        ClickVClickState.Foreground = c.Enabled ? (Brush)FindResource("SuccessBrush") : (Brush)FindResource("MutedBrush");\n'
    )

old_buttons = '''        var buttons = action == "boltpush"\n            ? new[] { BoltPushStable, BoltPushFast, BoltPushTurbo, BoltPushInstant }\n            : new[] { BoltsStable, BoltsFast, BoltsTurbo, BoltsInstant };'''
new_buttons = '''        var buttons = action switch\n        {\n            "boltpush" => new[] { BoltPushStable, BoltPushFast, BoltPushTurbo, BoltPushInstant },\n            "clickvclick" => new[] { ClickVClickStable, ClickVClickFast, ClickVClickTurbo, ClickVClickInstant },\n            _ => new[] { BoltsStable, BoltsFast, BoltsTurbo, BoltsInstant }\n        };'''
if old_buttons in s:
    s = s.replace(old_buttons, new_buttons)

if '_settings.Bolts.ClickVClick.Enabled' not in s:
    s = s.replace(
        '        _settings.Bolts.Bolts.Enabled = BoltsEnabled.IsChecked == true;\n',
        '        _settings.Bolts.Bolts.Enabled = BoltsEnabled.IsChecked == true;\n        _settings.Bolts.ClickVClick.Enabled = ClickVClickEnabled.IsChecked == true;\n'
    )

old_speed = '''        if (parts[0] == "boltpush") _settings.Bolts.BoltPush.SpeedMode = mode;\n        else _settings.Bolts.Bolts.SpeedMode = mode;'''
new_speed = '''        if (parts[0] == "boltpush") _settings.Bolts.BoltPush.SpeedMode = mode;\n        else if (parts[0] == "clickvclick") _settings.Bolts.ClickVClick.SpeedMode = mode;\n        else _settings.Bolts.Bolts.SpeedMode = mode;'''
if old_speed in s:
    s = s.replace(old_speed, new_speed)

if 'ClickVClickCoordinate_Changed' not in s:
    anchor = '''    private void TestBoltAction_Click(object sender, RoutedEventArgs e)\n'''
    method = '''    private void ClickVClickCoordinate_Changed(object sender, SelectionChangedEventArgs e)\n    {\n        if (_initializing) return;\n        _settings.Bolts.ClickVClick.CoordinateId = ClickVClickCoordinate.SelectedItem is CoordinateItem c ? c.Id : "";\n        Save();\n    }\n\n'''
    s = s.replace(anchor, method + anchor)

# Trigger third hotkey.
trigger_old = '''        var p = _settings.Bolts.BoltPush;\n        var b = _settings.Bolts.Bolts;\n        if (p.Enabled && string.Equals(p.Hotkey, key, StringComparison.OrdinalIgnoreCase))\n            _ = RunBoltActionAsync("boltpush");\n        if (b.Enabled && string.Equals(b.Hotkey, key, StringComparison.OrdinalIgnoreCase))\n            _ = RunBoltActionAsync("bolts");'''
trigger_new = '''        var p = _settings.Bolts.BoltPush;\n        var b = _settings.Bolts.Bolts;\n        var c = _settings.Bolts.ClickVClick;\n        if (p.Enabled && string.Equals(p.Hotkey, key, StringComparison.OrdinalIgnoreCase))\n            _ = RunBoltActionAsync("boltpush");\n        if (b.Enabled && string.Equals(b.Hotkey, key, StringComparison.OrdinalIgnoreCase))\n            _ = RunBoltActionAsync("bolts");\n        if (c.Enabled && string.Equals(c.Hotkey, key, StringComparison.OrdinalIgnoreCase))\n            _ = RunBoltActionAsync("clickvclick");'''
if trigger_old in s:
    s = s.replace(trigger_old, trigger_new)

if 'else if (action == "clickvclick")' not in s:
    anchor = '''        else if (action == "bolts")\n        {\n            var s = _settings.Bolts.Bolts;'''
    block = '''        else if (action == "clickvclick")\n        {\n            var cfg = _settings.Bolts.ClickVClick;\n            var coord = _settings.Coordinates.FirstOrDefault(c => c.Id == cfg.CoordinateId);\n            if (coord?.X is not int x || coord.Y is not int y)\n            {\n                Log("Click VVV Click: select a coordinate first.");\n                ShowPage("Macros");\n                return;\n            }\n            if (!await _clickVClickRun.WaitAsync(0)) return;\n            try\n            {\n                var t = BoltTiming.For(cfg.SpeedMode);\n                ClickVClickState.Text = "● RUNNING";\n\n                InputService.SetCursor(x, y);\n                await BoltDelay(t.PointerSettle);\n                InputService.MouseClickHeld("left", t.ClickHold, CancellationToken.None);\n                await BoltDelay(t.AfterClick);\n\n                await TapTripleVOrdered(t, beforeFinalShift: false);\n                if (t.FinalSafety > 0) await BoltDelay(t.FinalSafety);\n\n                InputService.SetCursor(x, y);\n                await BoltDelay(t.PointerSettle);\n                InputService.MouseClickHeld("left", t.ClickHold, CancellationToken.None);\n                await BoltDelay(t.AfterClick);\n                Log($"Click VVV Click · {cfg.SpeedMode.ToUpperInvariant()} · {x}, {y}");\n            }\n            finally\n            {\n                InputService.KeyUp("V");\n                _clickVClickRun.Release();\n                RefreshBoltsUi();\n            }\n        }\n        else if (action == "bolts")\n        {\n            var s = _settings.Bolts.Bolts;'''
    if anchor not in s:
        raise SystemExit('Bolts action anchor missing')
    s = s.replace(anchor, block)
save(p, s)

# --- UI card ---
p, s = rw('MainWindow.xaml')
if 'x:Name="ClickVClickEnabled"' not in s:
    page_start = s.find('<Grid x:Name="PageMacros"')
    page_end = s.find('<!-- WALLHOP PAGE -->', page_start)
    if page_start < 0 or page_end < 0:
        raise SystemExit('Bolts page not found')
    segment = s[page_start:page_end]
    insert_at = segment.rfind('</StackPanel>')
    if insert_at < 0:
        raise SystemExit('Bolts page stackpanel end missing')
    card = '''\n                                    <Border Style="{StaticResource CardBorder}" Margin="0,12,0,0">\n                                        <StackPanel>\n                                            <Grid><TextBlock Text="CLICK VVV CLICK" FontSize="17" FontWeight="Black" Foreground="{DynamicResource AccentBrush}"/><TextBlock x:Name="ClickVClickState" Text="○ OFF" HorizontalAlignment="Right" FontWeight="Bold"/></Grid>\n                                            <TextBlock Text="saved-coordinate click → V V V → saved-coordinate click" Foreground="{DynamicResource MutedBrush}" FontSize="10" Margin="0,5,0,12"/>\n                                            <CheckBox x:Name="ClickVClickEnabled" Content="ENABLE CLICK VVV CLICK" Style="{StaticResource RiuCheckBox}" Checked="BoltActionToggle_Changed" Unchecked="BoltActionToggle_Changed"/>\n                                            <Button x:Name="ClickVClickHotkeyButton" Content="HOTKEY · C" Style="{StaticResource RiuButton}" Margin="0,9,0,0" Click="HotkeyCapture_Click" Tag="clickvclick"/>\n                                            <TextBlock Text="COORDINATE" Foreground="{DynamicResource MutedBrush}" FontWeight="Bold" FontSize="9" Margin="0,12,0,5"/>\n                                            <ComboBox x:Name="ClickVClickCoordinate" Style="{StaticResource RiuComboBox}" SelectionChanged="ClickVClickCoordinate_Changed"/>\n                                            <TextBlock Text="SPEED" Foreground="{DynamicResource MutedBrush}" FontWeight="Bold" FontSize="9" Margin="0,12,0,4"/>\n                                            <UniformGrid Columns="4">\n                                                <Button x:Name="ClickVClickStable" Content="STABLE" Style="{StaticResource RiuButton}" Margin="2" Click="BoltSpeed_Click" Tag="clickvclick|stable"/>\n                                                <Button x:Name="ClickVClickFast" Content="FAST" Style="{StaticResource RiuButton}" Margin="2" Click="BoltSpeed_Click" Tag="clickvclick|fast"/>\n                                                <Button x:Name="ClickVClickTurbo" Content="TURBO" Style="{StaticResource RiuButton}" Margin="2" Click="BoltSpeed_Click" Tag="clickvclick|turbo"/>\n                                                <Button x:Name="ClickVClickInstant" Content="INSTANT" Style="{StaticResource RiuButton}" Margin="2" Click="BoltSpeed_Click" Tag="clickvclick|instant"/>\n                                            </UniformGrid>\n                                            <Button Content="▶ TEST CLICK VVV CLICK" Style="{StaticResource AccentButton}" Margin="0,10,0,0" Click="TestBoltAction_Click" Tag="clickvclick"/>\n                                        </StackPanel>\n                                    </Border>\n'''
    segment = segment[:insert_at] + card + segment[insert_at:]
    s = s[:page_start] + segment + s[page_end:]
save(p, s)

print('Added Click VVV Click built-in Bolts macro')
