from pathlib import Path

root = Path('src')

def rw(name):
    p = root / name
    return p, p.read_text(encoding='utf-8')

def save(p, s):
    p.write_text(s, encoding='utf-8')

# Extend generic bolt settings with a second coordinate and a locked snapshot.
p, s = rw('Models.cs')
if 'public string CoordinateId2' not in s:
    s = s.replace(
        '    public string CoordinateId { get; set; } = "";\n',
        '    public string CoordinateId { get; set; } = "";\n'
        '    public string CoordinateId2 { get; set; } = "";\n'
        '    public bool CoordinatesLocked { get; set; }\n'
        '    public int? FirstX { get; set; }\n'
        '    public int? FirstY { get; set; }\n'
        '    public int? SecondX { get; set; }\n'
        '    public int? SecondY { get; set; }\n'
    )
save(p, s)

# Replace the single-coordinate UI for CLICK VVV CLICK with two coordinates + reset.
p, s = rw('MainWindow.xaml')
old = '''                                            <TextBlock Text="COORDINATE" Foreground="{DynamicResource MutedBrush}" FontWeight="Bold" FontSize="9" Margin="0,12,0,5"/>\n                                            <ComboBox x:Name="ClickVClickCoordinate" Style="{StaticResource RiuComboBox}" SelectionChanged="ClickVClickCoordinate_Changed"/>'''
new = '''                                            <TextBlock Text="FIRST COORDINATE" Foreground="{DynamicResource MutedBrush}" FontWeight="Bold" FontSize="9" Margin="0,12,0,5"/>\n                                            <ComboBox x:Name="ClickVClickFirstCoordinate" Style="{StaticResource RiuComboBox}" SelectionChanged="ClickVClickFirstCoordinate_Changed"/>\n                                            <TextBlock Text="SECOND COORDINATE" Foreground="{DynamicResource MutedBrush}" FontWeight="Bold" FontSize="9" Margin="0,10,0,5"/>\n                                            <ComboBox x:Name="ClickVClickSecondCoordinate" Style="{StaticResource RiuComboBox}" SelectionChanged="ClickVClickSecondCoordinate_Changed"/>\n                                            <TextBlock x:Name="ClickVClickCoordsState" Text="SET BOTH COORDS · THEY LOCK AUTOMATICALLY" Foreground="{DynamicResource MutedBrush}" FontSize="9" Margin="0,8,0,0"/>\n                                            <Button Content="RESET COORDS" Style="{StaticResource RiuButton}" Margin="0,8,0,0" Click="ClickVClickResetCoords_Click"/>'''
if old not in s:
    raise SystemExit('single Click VVV Click coordinate UI not found')
s = s.replace(old, new)
save(p, s)

# Patch engine/UI sync.
p, s = rw('MainWindow.Bolts.cs')
old = '''        var selectedClick = ClickVClickCoordinate.SelectedItem as CoordinateItem;\n        ClickVClickCoordinate.ItemsSource = null;\n        ClickVClickCoordinate.ItemsSource = _settings.Coordinates;\n        ClickVClickCoordinate.DisplayMemberPath = nameof(CoordinateItem.Display);\n        ClickVClickCoordinate.SelectedItem = _settings.Coordinates.FirstOrDefault(x => x.Id == c.CoordinateId) ?? selectedClick;'''
new = '''        var selectedClick1 = ClickVClickFirstCoordinate.SelectedItem as CoordinateItem;\n        var selectedClick2 = ClickVClickSecondCoordinate.SelectedItem as CoordinateItem;\n        ClickVClickFirstCoordinate.ItemsSource = null;\n        ClickVClickSecondCoordinate.ItemsSource = null;\n        ClickVClickFirstCoordinate.ItemsSource = _settings.Coordinates;\n        ClickVClickSecondCoordinate.ItemsSource = _settings.Coordinates;\n        ClickVClickFirstCoordinate.DisplayMemberPath = nameof(CoordinateItem.Display);\n        ClickVClickSecondCoordinate.DisplayMemberPath = nameof(CoordinateItem.Display);\n        ClickVClickFirstCoordinate.SelectedItem = _settings.Coordinates.FirstOrDefault(x => x.Id == c.CoordinateId) ?? selectedClick1;\n        ClickVClickSecondCoordinate.SelectedItem = _settings.Coordinates.FirstOrDefault(x => x.Id == c.CoordinateId2) ?? selectedClick2;\n        ClickVClickFirstCoordinate.IsEnabled = !c.CoordinatesLocked;\n        ClickVClickSecondCoordinate.IsEnabled = !c.CoordinatesLocked;\n        ClickVClickCoordsState.Text = c.CoordinatesLocked\n            ? $"LOCKED · ({c.FirstX}, {c.FirstY}) → ({c.SecondX}, {c.SecondY})"\n            : "SET BOTH COORDS · THEY LOCK AUTOMATICALLY";'''
if old not in s:
    raise SystemExit('Click VVV Click refresh block not found')
s = s.replace(old, new)

old_handler = '''    private void ClickVClickCoordinate_Changed(object sender, SelectionChangedEventArgs e)\n    {\n        if (_initializing) return;\n        _settings.Bolts.ClickVClick.CoordinateId = ClickVClickCoordinate.SelectedItem is CoordinateItem c ? c.Id : "";\n        Save();\n    }\n\n'''
new_handler = '''    private void ClickVClickFirstCoordinate_Changed(object sender, SelectionChangedEventArgs e)\n    {\n        if (_initializing) return;\n        var cfg = _settings.Bolts.ClickVClick;\n        if (cfg.CoordinatesLocked) { RefreshBoltsUi(); return; }\n        cfg.CoordinateId = ClickVClickFirstCoordinate.SelectedItem is CoordinateItem c ? c.Id : "";\n        TryLockClickVClickCoordinates();\n        Save();\n    }\n\n    private void ClickVClickSecondCoordinate_Changed(object sender, SelectionChangedEventArgs e)\n    {\n        if (_initializing) return;\n        var cfg = _settings.Bolts.ClickVClick;\n        if (cfg.CoordinatesLocked) { RefreshBoltsUi(); return; }\n        cfg.CoordinateId2 = ClickVClickSecondCoordinate.SelectedItem is CoordinateItem c ? c.Id : "";\n        TryLockClickVClickCoordinates();\n        Save();\n    }\n\n    private void TryLockClickVClickCoordinates()\n    {\n        var cfg = _settings.Bolts.ClickVClick;\n        if (cfg.CoordinatesLocked || string.IsNullOrWhiteSpace(cfg.CoordinateId) || string.IsNullOrWhiteSpace(cfg.CoordinateId2)) return;\n        var first = _settings.Coordinates.FirstOrDefault(x => x.Id == cfg.CoordinateId);\n        var second = _settings.Coordinates.FirstOrDefault(x => x.Id == cfg.CoordinateId2);\n        if (first?.X is not int x1 || first.Y is not int y1 || second?.X is not int x2 || second.Y is not int y2) return;\n        cfg.FirstX = x1; cfg.FirstY = y1; cfg.SecondX = x2; cfg.SecondY = y2;\n        cfg.CoordinatesLocked = true;\n        Save();\n        RefreshBoltsUi();\n        Log($"Click VVV Click coords locked · {x1},{y1} → {x2},{y2}");\n    }\n\n    private void ClickVClickResetCoords_Click(object sender, RoutedEventArgs e)\n    {\n        var cfg = _settings.Bolts.ClickVClick;\n        cfg.CoordinatesLocked = false;\n        cfg.CoordinateId = ""; cfg.CoordinateId2 = "";\n        cfg.FirstX = null; cfg.FirstY = null; cfg.SecondX = null; cfg.SecondY = null;\n        Save();\n        RefreshBoltsUi();\n        Log("Click VVV Click coordinates reset.");\n    }\n\n'''
if old_handler not in s:
    raise SystemExit('single coordinate handler not found')
s = s.replace(old_handler, new_handler)

old_branch = '''            var cfg = _settings.Bolts.ClickVClick;\n            var coord = _settings.Coordinates.FirstOrDefault(c => c.Id == cfg.CoordinateId);\n            if (coord?.X is not int x || coord.Y is not int y)\n            {\n                Log("Click VVV Click: select a coordinate first.");\n                ShowPage("Macros");\n                return;\n            }\n            if (!await _clickVClickRun.WaitAsync(0)) return;\n            try\n            {\n                var t = BoltTiming.For(cfg.SpeedMode);\n                ClickVClickState.Text = "● RUNNING";\n\n                InputService.SetCursor(x, y);\n                await BoltDelay(t.PointerSettle);\n                InputService.MouseClickHeld("left", t.ClickHold, CancellationToken.None);\n                await BoltDelay(t.AfterClick);\n\n                await TapTripleVOrdered(t, beforeFinalShift: false);\n                if (t.FinalSafety > 0) await BoltDelay(t.FinalSafety);\n\n                InputService.SetCursor(x, y);\n                await BoltDelay(t.PointerSettle);\n                InputService.MouseClickHeld("left", t.ClickHold, CancellationToken.None);\n                await BoltDelay(t.AfterClick);\n                Log($"Click VVV Click · {cfg.SpeedMode.ToUpperInvariant()} · {x}, {y}");'''
new_branch = '''            var cfg = _settings.Bolts.ClickVClick;\n            if (!cfg.CoordinatesLocked || cfg.FirstX is not int x1 || cfg.FirstY is not int y1 || cfg.SecondX is not int x2 || cfg.SecondY is not int y2)\n            {\n                Log("Click VVV Click: set both coordinates first.");\n                ShowPage("Macros");\n                return;\n            }\n            if (!await _clickVClickRun.WaitAsync(0)) return;\n            try\n            {\n                var t = BoltTiming.For(cfg.SpeedMode);\n                ClickVClickState.Text = "● RUNNING";\n\n                InputService.SetCursor(x1, y1);\n                await BoltDelay(t.PointerSettle);\n                InputService.MouseClickHeld("left", t.ClickHold, CancellationToken.None);\n                await BoltDelay(t.AfterClick);\n\n                await TapTripleVOrdered(t, beforeFinalShift: false);\n                if (t.FinalSafety > 0) await BoltDelay(t.FinalSafety);\n\n                InputService.SetCursor(x2, y2);\n                await BoltDelay(t.PointerSettle);\n                InputService.MouseClickHeld("left", t.ClickHold, CancellationToken.None);\n                await BoltDelay(t.AfterClick);\n                Log($"Click VVV Click · {cfg.SpeedMode.ToUpperInvariant()} · {x1},{y1} → {x2},{y2}");'''
if old_branch not in s:
    raise SystemExit('single-coordinate run branch not found')
s = s.replace(old_branch, new_branch)
save(p, s)

print('Applied locked dual-coordinate Click VVV Click patch')
