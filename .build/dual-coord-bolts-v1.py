from pathlib import Path

root = Path('src')

def rw(name):
    p = root / name
    return p, p.read_text(encoding='utf-8')

def save(p, s):
    p.write_text(s, encoding='utf-8')

# ---- SETTINGS MODEL ----
p, s = rw('Models.cs')
s = s.replace(
'''public sealed class BoltMacroSettings
{
    public bool Enabled { get; set; }
    public string Hotkey { get; set; } = "";
    public string SpeedMode { get; set; } = "fast";
    public string CoordinateId { get; set; } = "";
}''',
'''public sealed class BoltMacroSettings
{
    public bool Enabled { get; set; }
    public string Hotkey { get; set; } = "";
    public string SpeedMode { get; set; } = "fast";
    public string CoordinateId { get; set; } = "";
    public string SecondaryCoordinateId { get; set; } = "";
    public int? FirstX { get; set; }
    public int? FirstY { get; set; }
    public int? SecondX { get; set; }
    public int? SecondY { get; set; }
    public bool CoordinatesLocked { get; set; }
}''')
s = s.replace(
'''public sealed class BoltsSettings
{
    public BoltMacroSettings BoltPush { get; set; } = new() { Hotkey = "E" };
    public BoltMacroSettings Bolts { get; set; } = new() { Hotkey = "V" };
}''',
'''public sealed class BoltsSettings
{
    public BoltMacroSettings BoltPush { get; set; } = new() { Hotkey = "E" };
    public BoltMacroSettings Bolts { get; set; } = new() { Hotkey = "V" };
    public BoltMacroSettings DualCoord { get; set; } = new() { Hotkey = "Q" };
}''')
s = s.replace(
'''        s.Bolts.BoltPush ??= new() { Hotkey = "E" };
        s.Bolts.Bolts ??= new() { Hotkey = "V" };
        s.Bolts.BoltPush.SpeedMode = NormalizeBoltSpeed(s.Bolts.BoltPush.SpeedMode);
        s.Bolts.Bolts.SpeedMode = NormalizeBoltSpeed(s.Bolts.Bolts.SpeedMode);''',
'''        s.Bolts.BoltPush ??= new() { Hotkey = "E" };
        s.Bolts.Bolts ??= new() { Hotkey = "V" };
        s.Bolts.DualCoord ??= new() { Hotkey = "Q" };
        s.Bolts.BoltPush.SpeedMode = NormalizeBoltSpeed(s.Bolts.BoltPush.SpeedMode);
        s.Bolts.Bolts.SpeedMode = NormalizeBoltSpeed(s.Bolts.Bolts.SpeedMode);
        s.Bolts.DualCoord.SpeedMode = NormalizeBoltSpeed(s.Bolts.DualCoord.SpeedMode);''')
save(p, s)

# ---- PHYSICAL HOTKEY ROUTING / CAPTURE ----
p, s = rw('MainWindow.Extras.cs')
s = s.replace(
'''        var boltMatched = (_settings.Bolts.BoltPush.Enabled && string.Equals(_settings.Bolts.BoltPush.Hotkey, key, StringComparison.OrdinalIgnoreCase)) ||
                          (_settings.Bolts.Bolts.Enabled && string.Equals(_settings.Bolts.Bolts.Hotkey, key, StringComparison.OrdinalIgnoreCase));''',
'''        var boltMatched = (_settings.Bolts.BoltPush.Enabled && string.Equals(_settings.Bolts.BoltPush.Hotkey, key, StringComparison.OrdinalIgnoreCase)) ||
                          (_settings.Bolts.Bolts.Enabled && string.Equals(_settings.Bolts.Bolts.Hotkey, key, StringComparison.OrdinalIgnoreCase)) ||
                          (_settings.Bolts.DualCoord.Enabled && string.Equals(_settings.Bolts.DualCoord.Hotkey, key, StringComparison.OrdinalIgnoreCase));''')
s = s.replace(
'''        else if (target == "boltpush") _settings.Bolts.BoltPush.Hotkey = key;
        else if (target == "bolts") _settings.Bolts.Bolts.Hotkey = key;''',
'''        else if (target == "boltpush") _settings.Bolts.BoltPush.Hotkey = key;
        else if (target == "bolts") _settings.Bolts.Bolts.Hotkey = key;
        else if (target == "dualcoord") _settings.Bolts.DualCoord.Hotkey = key;''')
save(p, s)

# ---- BOLTS ENGINE ----
p, s = rw('MainWindow.Bolts.cs')
s = s.replace('    private readonly SemaphoreSlim _boltsRun = new(1, 1);', '    private readonly SemaphoreSlim _boltsRun = new(1, 1);\n    private readonly SemaphoreSlim _dualCoordRun = new(1, 1);')

s = s.replace(
'''        var p = _settings.Bolts.BoltPush;
        var b = _settings.Bolts.Bolts;

        BoltPushEnabled.IsChecked = p.Enabled;
        BoltsEnabled.IsChecked = b.Enabled;''',
'''        var p = _settings.Bolts.BoltPush;
        var b = _settings.Bolts.Bolts;
        var d = _settings.Bolts.DualCoord;

        BoltPushEnabled.IsChecked = p.Enabled;
        BoltsEnabled.IsChecked = b.Enabled;
        DualCoordEnabled.IsChecked = d.Enabled;''')

s = s.replace(
'''        BoltPushHotkeyButton.Content = $"HOTKEY · {(string.IsNullOrWhiteSpace(p.Hotkey) ? "NONE" : p.Hotkey)}";
        BoltsHotkeyButton.Content = $"HOTKEY · {(string.IsNullOrWhiteSpace(b.Hotkey) ? "NONE" : b.Hotkey)}";''',
'''        BoltPushHotkeyButton.Content = $"HOTKEY · {(string.IsNullOrWhiteSpace(p.Hotkey) ? "NONE" : p.Hotkey)}";
        BoltsHotkeyButton.Content = $"HOTKEY · {(string.IsNullOrWhiteSpace(b.Hotkey) ? "NONE" : b.Hotkey)}";
        DualCoordHotkeyButton.Content = $"HOTKEY · {(string.IsNullOrWhiteSpace(d.Hotkey) ? "NONE" : d.Hotkey)}";''')

anchor = '''        BoltPushCoordinate.SelectedItem = _settings.Coordinates.FirstOrDefault(c => c.Id == p.CoordinateId) ?? selected;

        PaintBoltSpeedButtons("boltpush", p.SpeedMode);'''
insert = '''        BoltPushCoordinate.SelectedItem = _settings.Coordinates.FirstOrDefault(c => c.Id == p.CoordinateId) ?? selected;

        DualCoordFirst.ItemsSource = null;
        DualCoordSecond.ItemsSource = null;
        DualCoordFirst.ItemsSource = _settings.Coordinates;
        DualCoordSecond.ItemsSource = _settings.Coordinates;
        DualCoordFirst.DisplayMemberPath = nameof(CoordinateItem.Display);
        DualCoordSecond.DisplayMemberPath = nameof(CoordinateItem.Display);
        DualCoordFirst.SelectedItem = _settings.Coordinates.FirstOrDefault(c => c.Id == d.CoordinateId);
        DualCoordSecond.SelectedItem = _settings.Coordinates.FirstOrDefault(c => c.Id == d.SecondaryCoordinateId);
        DualCoordFirst.IsEnabled = !d.CoordinatesLocked;
        DualCoordSecond.IsEnabled = !d.CoordinatesLocked;
        DualCoordReset.IsEnabled = d.CoordinatesLocked || !string.IsNullOrWhiteSpace(d.CoordinateId) || !string.IsNullOrWhiteSpace(d.SecondaryCoordinateId);
        DualCoordLockState.Text = d.CoordinatesLocked && d.FirstX is int fx && d.FirstY is int fy && d.SecondX is int sx && d.SecondY is int sy
            ? $"LOCKED · {fx},{fy} → {sx},{sy}"
            : "SELECT BOTH COORDS";

        PaintBoltSpeedButtons("boltpush", p.SpeedMode);'''
if anchor not in s:
    raise SystemExit('Refresh coordinate anchor missing')
s = s.replace(anchor, insert)
s = s.replace('        PaintBoltSpeedButtons("bolts", b.SpeedMode);', '        PaintBoltSpeedButtons("bolts", b.SpeedMode);\n        PaintBoltSpeedButtons("dualcoord", d.SpeedMode);')
s = s.replace(
'''        BoltsState.Text = b.Enabled ? "● ARMED" : "○ OFF";
        BoltPushState.Foreground = p.Enabled ? (Brush)FindResource("SuccessBrush") : (Brush)FindResource("MutedBrush");
        BoltsState.Foreground = b.Enabled ? (Brush)FindResource("SuccessBrush") : (Brush)FindResource("MutedBrush");''',
'''        BoltsState.Text = b.Enabled ? "● ARMED" : "○ OFF";
        DualCoordState.Text = d.Enabled ? "● ARMED" : "○ OFF";
        BoltPushState.Foreground = p.Enabled ? (Brush)FindResource("SuccessBrush") : (Brush)FindResource("MutedBrush");
        BoltsState.Foreground = b.Enabled ? (Brush)FindResource("SuccessBrush") : (Brush)FindResource("MutedBrush");
        DualCoordState.Foreground = d.Enabled ? (Brush)FindResource("SuccessBrush") : (Brush)FindResource("MutedBrush");''')

old_paint = '''        var buttons = action == "boltpush"
            ? new[] { BoltPushStable, BoltPushFast, BoltPushTurbo, BoltPushInstant }
            : new[] { BoltsStable, BoltsFast, BoltsTurbo, BoltsInstant };'''
new_paint = '''        var buttons = action switch
        {
            "boltpush" => new[] { BoltPushStable, BoltPushFast, BoltPushTurbo, BoltPushInstant },
            "dualcoord" => new[] { DualCoordStable, DualCoordFast, DualCoordTurbo, DualCoordInstant },
            _ => new[] { BoltsStable, BoltsFast, BoltsTurbo, BoltsInstant }
        };'''
if old_paint not in s:
    raise SystemExit('Paint button anchor missing')
s = s.replace(old_paint, new_paint)

s = s.replace(
'''        _settings.Bolts.BoltPush.Enabled = BoltPushEnabled.IsChecked == true;
        _settings.Bolts.Bolts.Enabled = BoltsEnabled.IsChecked == true;''',
'''        _settings.Bolts.BoltPush.Enabled = BoltPushEnabled.IsChecked == true;
        _settings.Bolts.Bolts.Enabled = BoltsEnabled.IsChecked == true;
        _settings.Bolts.DualCoord.Enabled = DualCoordEnabled.IsChecked == true;''')

s = s.replace(
'''        if (parts[0] == "boltpush") _settings.Bolts.BoltPush.SpeedMode = mode;
        else _settings.Bolts.Bolts.SpeedMode = mode;''',
'''        if (parts[0] == "boltpush") _settings.Bolts.BoltPush.SpeedMode = mode;
        else if (parts[0] == "dualcoord") _settings.Bolts.DualCoord.SpeedMode = mode;
        else _settings.Bolts.Bolts.SpeedMode = mode;''')

method_anchor = '''    private void TestBoltAction_Click(object sender, RoutedEventArgs e)
    {
        if (sender is Button b) _ = RunBoltActionAsync(b.Tag?.ToString() ?? "");
    }
'''
new_methods = method_anchor + '''
    private void DualCoordCoordinate_Changed(object sender, SelectionChangedEventArgs e)
    {
        if (_initializing) return;
        var d = _settings.Bolts.DualCoord;
        if (d.CoordinatesLocked) { RefreshBoltsUi(); return; }
        d.CoordinateId = DualCoordFirst.SelectedItem is CoordinateItem a ? a.Id : "";
        d.SecondaryCoordinateId = DualCoordSecond.SelectedItem is CoordinateItem b ? b.Id : "";
        if (DualCoordFirst.SelectedItem is CoordinateItem first && DualCoordSecond.SelectedItem is CoordinateItem second &&
            first.X is int x1 && first.Y is int y1 && second.X is int x2 && second.Y is int y2)
        {
            d.FirstX = x1; d.FirstY = y1;
            d.SecondX = x2; d.SecondY = y2;
            d.CoordinatesLocked = true;
            Log($"Dual Coord locked · {x1},{y1} → {x2},{y2}");
        }
        Save();
        RefreshBoltsUi();
    }

    private void DualCoordReset_Click(object sender, RoutedEventArgs e)
    {
        var d = _settings.Bolts.DualCoord;
        d.CoordinatesLocked = false;
        d.CoordinateId = "";
        d.SecondaryCoordinateId = "";
        d.FirstX = d.FirstY = d.SecondX = d.SecondY = null;
        Save();
        RefreshBoltsUi();
        Log("Dual Coord coordinates unlocked and cleared.");
    }
'''
if method_anchor not in s:
    raise SystemExit('Test action anchor missing')
s = s.replace(method_anchor, new_methods)

s = s.replace(
'''        var p = _settings.Bolts.BoltPush;
        var b = _settings.Bolts.Bolts;
        if (p.Enabled && string.Equals(p.Hotkey, key, StringComparison.OrdinalIgnoreCase))
            _ = RunBoltActionAsync("boltpush");
        if (b.Enabled && string.Equals(b.Hotkey, key, StringComparison.OrdinalIgnoreCase))
            _ = RunBoltActionAsync("bolts");''',
'''        var p = _settings.Bolts.BoltPush;
        var b = _settings.Bolts.Bolts;
        var d = _settings.Bolts.DualCoord;
        if (p.Enabled && string.Equals(p.Hotkey, key, StringComparison.OrdinalIgnoreCase))
            _ = RunBoltActionAsync("boltpush");
        if (b.Enabled && string.Equals(b.Hotkey, key, StringComparison.OrdinalIgnoreCase))
            _ = RunBoltActionAsync("bolts");
        if (d.Enabled && string.Equals(d.Hotkey, key, StringComparison.OrdinalIgnoreCase))
            _ = RunBoltActionAsync("dualcoord");''')

branch_anchor = '''        else if (action == "bolts")
        {
            var s = _settings.Bolts.Bolts;'''
dual_branch = '''        else if (action == "dualcoord")
        {
            var s = _settings.Bolts.DualCoord;
            if (!s.CoordinatesLocked || s.FirstX is not int x1 || s.FirstY is not int y1 || s.SecondX is not int x2 || s.SecondY is not int y2)
            {
                Log("Dual Coord: select both coordinates first.");
                return;
            }
            if (!await _dualCoordRun.WaitAsync(0)) return;
            try
            {
                var t = BoltTiming.For(s.SpeedMode);
                DualCoordState.Text = "● RUNNING";
                InputService.SetCursor(x1, y1);
                if (t.PointerSettle > 0) await BoltDelay(Math.Max(t.PointerSettle, 6));
                InputService.MouseClickHeld("left", s.SpeedMode is "turbo" or "instant" ? 12 : 14, CancellationToken.None);
                if (t.StepGap > 0) await BoltDelay(Math.Max(t.StepGap, 5));
                await TapTripleVOrdered(t, beforeFinalShift: false);
                if (t.FinalSafety > 0) await BoltDelay(Math.Max(t.FinalSafety, 6));
                InputService.SetCursor(x2, y2);
                if (t.PointerSettle > 0) await BoltDelay(Math.Max(t.PointerSettle, 6));
                InputService.MouseClickHeld("left", s.SpeedMode is "turbo" or "instant" ? 12 : 14, CancellationToken.None);
                Log($"Dual Coord · {s.SpeedMode.ToUpperInvariant()} · {x1},{y1} → VVV → {x2},{y2}");
            }
            finally
            {
                InputService.KeyUp("V");
                _dualCoordRun.Release();
                RefreshBoltsUi();
            }
        }
        else if (action == "bolts")
        {
            var s = _settings.Bolts.Bolts;'''
if branch_anchor not in s:
    raise SystemExit('Bolts branch anchor missing')
s = s.replace(branch_anchor, dual_branch)
save(p, s)

# ---- UI: third macro card ----
p, s = rw('MainWindow.xaml')
needle = '''                                                <Button Content="▶ TEST BOLTS" Style="{StaticResource AccentButton}" Margin="0,10,0,0" Click="TestBoltAction_Click" Tag="bolts"/>
                                            </StackPanel>
                                        </Border>
                                    </Grid>
                                </StackPanel>'''
replacement = '''                                                <Button Content="▶ TEST BOLTS" Style="{StaticResource AccentButton}" Margin="0,10,0,0" Click="TestBoltAction_Click" Tag="bolts"/>
                                            </StackPanel>
                                        </Border>
                                    </Grid>
                                    <Border Style="{StaticResource CardBorder}" Margin="0,12,0,0">
                                        <StackPanel>
                                            <Grid>
                                                <TextBlock Text="DOUBLE COORD VVV" FontSize="17" FontWeight="Black" Foreground="{DynamicResource AccentBrush}"/>
                                                <TextBlock x:Name="DualCoordState" Text="○ OFF" HorizontalAlignment="Right" FontWeight="Bold"/>
                                            </Grid>
                                            <TextBlock Text="coordinate 1 click → V V V → coordinate 2 click" Foreground="{DynamicResource MutedBrush}" FontSize="10" Margin="0,5,0,10"/>
                                            <CheckBox x:Name="DualCoordEnabled" Content="ENABLE DOUBLE COORD" Style="{StaticResource RiuCheckBox}" Checked="BoltActionToggle_Changed" Unchecked="BoltActionToggle_Changed"/>
                                            <Button x:Name="DualCoordHotkeyButton" Content="HOTKEY · Q" Style="{StaticResource RiuButton}" Margin="0,9,0,0" Click="HotkeyCapture_Click" Tag="dualcoord"/>
                                            <Grid Margin="0,12,0,0">
                                                <Grid.ColumnDefinitions><ColumnDefinition/><ColumnDefinition Width="10"/><ColumnDefinition/></Grid.ColumnDefinitions>
                                                <StackPanel Grid.Column="0">
                                                    <TextBlock Text="FIRST COORDINATE" Foreground="{DynamicResource MutedBrush}" FontWeight="Bold" FontSize="9" Margin="0,0,0,5"/>
                                                    <ComboBox x:Name="DualCoordFirst" Style="{StaticResource RiuComboBox}" SelectionChanged="DualCoordCoordinate_Changed"/>
                                                </StackPanel>
                                                <StackPanel Grid.Column="2">
                                                    <TextBlock Text="SECOND COORDINATE" Foreground="{DynamicResource MutedBrush}" FontWeight="Bold" FontSize="9" Margin="0,0,0,5"/>
                                                    <ComboBox x:Name="DualCoordSecond" Style="{StaticResource RiuComboBox}" SelectionChanged="DualCoordCoordinate_Changed"/>
                                                </StackPanel>
                                            </Grid>
                                            <Grid Margin="0,9,0,0">
                                                <TextBlock x:Name="DualCoordLockState" Text="SELECT BOTH COORDS" Foreground="{DynamicResource MutedBrush}" FontWeight="Bold" FontSize="10" VerticalAlignment="Center"/>
                                                <Button x:Name="DualCoordReset" Content="RESET COORDS" Style="{StaticResource RiuButton}" HorizontalAlignment="Right" Width="150" Click="DualCoordReset_Click"/>
                                            </Grid>
                                            <TextBlock Text="After both points are selected, exact X/Y values are locked. They cannot change until RESET COORDS is pressed." Foreground="{DynamicResource MutedBrush}" FontSize="9" Margin="0,7,0,0" TextWrapping="Wrap"/>
                                            <TextBlock Text="SPEED" Foreground="{DynamicResource MutedBrush}" FontWeight="Bold" FontSize="9" Margin="0,12,0,4"/>
                                            <UniformGrid Columns="4">
                                                <Button x:Name="DualCoordStable" Content="STABLE" Style="{StaticResource RiuButton}" Margin="2" Click="BoltSpeed_Click" Tag="dualcoord|stable"/>
                                                <Button x:Name="DualCoordFast" Content="FAST" Style="{StaticResource RiuButton}" Margin="2" Click="BoltSpeed_Click" Tag="dualcoord|fast"/>
                                                <Button x:Name="DualCoordTurbo" Content="TURBO" Style="{StaticResource RiuButton}" Margin="2" Click="BoltSpeed_Click" Tag="dualcoord|turbo"/>
                                                <Button x:Name="DualCoordInstant" Content="INSTANT" Style="{StaticResource RiuButton}" Margin="2" Click="BoltSpeed_Click" Tag="dualcoord|instant"/>
                                            </UniformGrid>
                                            <Button Content="▶ TEST DOUBLE COORD" Style="{StaticResource AccentButton}" Margin="0,10,0,0" Click="TestBoltAction_Click" Tag="dualcoord"/>
                                        </StackPanel>
                                    </Border>
                                </StackPanel>'''
if needle not in s:
    raise SystemExit('Bolts UI insertion anchor missing')
s = s.replace(needle, replacement)
save(p, s)

print('Applied double-coordinate VVV macro with snapshot coordinate locking')
