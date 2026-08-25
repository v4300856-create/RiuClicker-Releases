using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;

namespace RiuClickerCS;

public partial class MainWindow
{
    private readonly SemaphoreSlim _boltPushRun = new(1, 1);
    private readonly SemaphoreSlim _boltsRun = new(1, 1);

    private void InitializeBoltsFeatures()
    {
        RefreshBoltsUi();
    }

    private void RefreshBoltsUi()
    {
        if (BoltPushEnabled is null) return;
        _initializing = true;
        var p = _settings.Bolts.BoltPush;
        var b = _settings.Bolts.Bolts;

        BoltPushEnabled.IsChecked = p.Enabled;
        BoltsEnabled.IsChecked = b.Enabled;
        BoltPushHotkeyButton.Content = $"HOTKEY · {(string.IsNullOrWhiteSpace(p.Hotkey) ? "NONE" : p.Hotkey)}";
        BoltsHotkeyButton.Content = $"HOTKEY · {(string.IsNullOrWhiteSpace(b.Hotkey) ? "NONE" : b.Hotkey)}";

        var selected = BoltPushCoordinate.SelectedItem as CoordinateItem;
        BoltPushCoordinate.ItemsSource = null;
        BoltPushCoordinate.ItemsSource = _settings.Coordinates;
        BoltPushCoordinate.DisplayMemberPath = nameof(CoordinateItem.Display);
        BoltPushCoordinate.SelectedItem = _settings.Coordinates.FirstOrDefault(c => c.Id == p.CoordinateId) ?? selected;

        PaintBoltSpeedButtons("boltpush", p.SpeedMode);
        PaintBoltSpeedButtons("bolts", b.SpeedMode);

        BoltPushState.Text = p.Enabled ? "● ARMED" : "○ OFF";
        BoltsState.Text = b.Enabled ? "● ARMED" : "○ OFF";
        BoltPushState.Foreground = p.Enabled ? (Brush)FindResource("SuccessBrush") : (Brush)FindResource("MutedBrush");
        BoltsState.Foreground = b.Enabled ? (Brush)FindResource("SuccessBrush") : (Brush)FindResource("MutedBrush");
        _initializing = false;
    }

    private void PaintBoltSpeedButtons(string action, string selected)
    {
        var buttons = action == "boltpush"
            ? new[] { BoltPushStable, BoltPushFast, BoltPushTurbo, BoltPushInstant }
            : new[] { BoltsStable, BoltsFast, BoltsTurbo, BoltsInstant };

        foreach (var button in buttons)
        {
            var tag = button.Tag?.ToString()?.Split('|').LastOrDefault() ?? "fast";
            button.BorderBrush = tag == selected ? (Brush)FindResource("AccentBrush") : (Brush)FindResource("LineBrush");
            button.Background = tag == selected
                ? new SolidColorBrush(Color.FromArgb(42, CurrentAccentColor().R, CurrentAccentColor().G, CurrentAccentColor().B))
                : (Brush)FindResource("ControlBrush");
        }
    }

    private void BoltActionToggle_Changed(object sender, RoutedEventArgs e)
    {
        if (_initializing) return;
        _settings.Bolts.BoltPush.Enabled = BoltPushEnabled.IsChecked == true;
        _settings.Bolts.Bolts.Enabled = BoltsEnabled.IsChecked == true;
        Save();
        RefreshBoltsUi();
    }

    private void BoltSpeed_Click(object sender, RoutedEventArgs e)
    {
        if (sender is not Button b || b.Tag?.ToString()?.Split('|') is not { Length: 2 } parts) return;
        var mode = parts[1] is "stable" or "fast" or "turbo" or "instant" ? parts[1] : "fast";
        if (parts[0] == "boltpush") _settings.Bolts.BoltPush.SpeedMode = mode;
        else _settings.Bolts.Bolts.SpeedMode = mode;
        Save();
        RefreshBoltsUi();
    }

    private void BoltPushCoordinate_Changed(object sender, SelectionChangedEventArgs e)
    {
        if (_initializing) return;
        _settings.Bolts.BoltPush.CoordinateId = BoltPushCoordinate.SelectedItem is CoordinateItem c ? c.Id : "";
        Save();
    }

    private void TestBoltAction_Click(object sender, RoutedEventArgs e)
    {
        if (sender is Button b) _ = RunBoltActionAsync(b.Tag?.ToString() ?? "");
    }

    private void TriggerBoltHotkey(string key)
    {
        var p = _settings.Bolts.BoltPush;
        var b = _settings.Bolts.Bolts;
        if (p.Enabled && string.Equals(p.Hotkey, key, StringComparison.OrdinalIgnoreCase))
            _ = RunBoltActionAsync("boltpush");
        if (b.Enabled && string.Equals(b.Hotkey, key, StringComparison.OrdinalIgnoreCase))
            _ = RunBoltActionAsync("bolts");
    }

    private async Task TapTripleVOrdered(BoltTiming t, bool beforeFinalShift)
    {
        var hold = Math.Max(1, t.KeyHold);
        var gap = Math.Max(0, t.StepGap);
        for (var i = 0; i < 3; i++)
        {
            InputService.KeyDown("V");
            await BoltDelay(hold).ConfigureAwait(true);
            InputService.KeyUp("V");
            if (i < 2 && gap > 0) await BoltDelay(gap).ConfigureAwait(true);
        }
        InputService.KeyUp("V");
        if (beforeFinalShift && t.FinalBarrier > 0) await BoltDelay(t.FinalBarrier).ConfigureAwait(true);
    }

    private async Task RunBoltActionAsync(string action)
    {
        if (action == "boltpush")
        {
            var s = _settings.Bolts.BoltPush;
            var coord = _settings.Coordinates.FirstOrDefault(c => c.Id == s.CoordinateId);
            if (coord?.X is not int x || coord.Y is not int y)
            {
                Log("Bolt Push: select a coordinate first.");
                ShowPage("Macros");
                return;
            }
            if (!await _boltPushRun.WaitAsync(0)) return;
            try
            {
                var t = BoltTiming.For(s.SpeedMode);
                BoltPushState.Text = "● RUNNING";

                // Exact requested order: Shift -> V V V -> Shift -> saved-coordinate click.
                InputService.TapKey("SHIFT", t.ModifierHold, CancellationToken.None);
                if (t.StepGap > 0) await BoltDelay(t.StepGap);
                await TapTripleVOrdered(t, beforeFinalShift: true);
                InputService.TapKey("SHIFT", t.ModifierHold, CancellationToken.None);
                InputService.KeyUp("V");
                InputService.KeyUp("SHIFT");
                if (t.FinalSafety > 0) await BoltDelay(t.FinalSafety);
                InputService.SetCursor(x, y);
                if (t.PointerSettle > 0) await BoltDelay(t.PointerSettle);
                InputService.MouseClick("left");
                Log($"Bolt Push · {s.SpeedMode.ToUpperInvariant()} · {x}, {y}");
            }
            finally
            {
                InputService.KeyUp("V");
                InputService.KeyUp("SHIFT");
                _boltPushRun.Release();
                RefreshBoltsUi();
            }
        }
        else if (action == "bolts")
        {
            var s = _settings.Bolts.Bolts;
            if (!await _boltsRun.WaitAsync(0)) return;
            try
            {
                var t = BoltTiming.For(s.SpeedMode);
                BoltsState.Text = "● RUNNING";
                await TapTripleVOrdered(t, beforeFinalShift: false);
                Log($"Bolts · {s.SpeedMode.ToUpperInvariant()}");
            }
            finally
            {
                InputService.KeyUp("V");
                _boltsRun.Release();
                RefreshBoltsUi();
            }
        }
    }

    private static Task BoltDelay(int ms) => ms <= 0 ? Task.CompletedTask : Task.Delay(ms);

    private readonly record struct BoltTiming(int KeyHold, int ModifierHold, int StepGap, int PointerSettle, int FinalBarrier, int FinalSafety)
    {
        public static BoltTiming For(string mode) => mode switch
        {
            "stable" => new(24, 50, 22, 28, 16, 16),
            "turbo" => new(4, 10, 2, 5, 4, 5),
            "instant" => new(1, 4, 0, 1, 2, 3),
            _ => new(10, 24, 7, 10, 8, 8)
        };
    }
}
