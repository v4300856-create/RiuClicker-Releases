using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;

namespace RiuClickerCS;

public partial class MainWindow
{
    private readonly SquadSyncService _squad = new();
    private readonly SemaphoreSlim _boltPushRun = new(1, 1);
    private readonly SemaphoreSlim _boltsRun = new(1, 1);

    private void InitializeProFeatures()
    {
        _squad.StatusChanged += m => Dispatcher.BeginInvoke(() => { SquadStatusText.Text = m; Log(m); });
        _squad.MembersChanged += () => Dispatcher.BeginInvoke(RefreshSquadUi);
        _squad.CommandReceived += key => Dispatcher.BeginInvoke(() => TriggerProHotkey(key, remote: true));
        RefreshProUi();
        RefreshSquadUi();
    }

    private void RefreshProUi()
    {
        if (BoltPushEnabled is null) return;
        _initializing = true;
        var p = _settings.ProActions.BoltPush;
        var b = _settings.ProActions.Bolts;
        BoltPushEnabled.IsChecked = p.Enabled;
        BoltsEnabled.IsChecked = b.Enabled;
        BoltPushHotkeyButton.Content = $"HOTKEY · {(string.IsNullOrWhiteSpace(p.Hotkey) ? "NONE" : p.Hotkey)}";
        BoltsHotkeyButton.Content = $"HOTKEY · {(string.IsNullOrWhiteSpace(b.Hotkey) ? "NONE" : b.Hotkey)}";
        var selected = BoltPushCoordinate.SelectedItem as CoordinateItem;
        BoltPushCoordinate.ItemsSource = null;
        BoltPushCoordinate.ItemsSource = _settings.Coordinates;
        BoltPushCoordinate.DisplayMemberPath = nameof(CoordinateItem.Display);
        BoltPushCoordinate.SelectedItem = _settings.Coordinates.FirstOrDefault(c => c.Id == p.CoordinateId) ?? selected;
        PaintSpeedButtons("boltpush", p.SpeedMode);
        PaintSpeedButtons("bolts", b.SpeedMode);
        BoltPushState.Text = p.Enabled ? "● ARMED" : "○ OFF";
        BoltsState.Text = b.Enabled ? "● ARMED" : "○ OFF";
        BoltPushState.Foreground = p.Enabled ? (Brush)FindResource("SuccessBrush") : (Brush)FindResource("MutedBrush");
        BoltsState.Foreground = b.Enabled ? (Brush)FindResource("SuccessBrush") : (Brush)FindResource("MutedBrush");
        _initializing = false;
    }

    private void PaintSpeedButtons(string action, string selected)
    {
        var buttons = action == "boltpush"
            ? new[] { BoltPushStable, BoltPushFast, BoltPushTurbo, BoltPushInstant }
            : new[] { BoltsStable, BoltsFast, BoltsTurbo, BoltsInstant };
        foreach (var button in buttons)
        {
            var tag = button.Tag?.ToString()?.Split('|').LastOrDefault() ?? "fast";
            button.BorderBrush = tag == selected ? (Brush)FindResource("AccentBrush") : (Brush)FindResource("LineBrush");
            button.Background = tag == selected ? new SolidColorBrush(Color.FromArgb(42, CurrentAccentColor().R, CurrentAccentColor().G, CurrentAccentColor().B)) : (Brush)FindResource("ControlBrush");
        }
    }

    private void ProActionToggle_Changed(object sender, RoutedEventArgs e)
    {
        if (_initializing) return;
        if (sender == BoltPushEnabled && BoltPushEnabled.IsChecked == true)
        {
            _settings.ProActions.BoltPush.Enabled = true;
            _settings.ProActions.Bolts.Enabled = false;
        }
        else if (sender == BoltsEnabled && BoltsEnabled.IsChecked == true)
        {
            _settings.ProActions.Bolts.Enabled = true;
            _settings.ProActions.BoltPush.Enabled = false;
        }
        else
        {
            _settings.ProActions.BoltPush.Enabled = BoltPushEnabled.IsChecked == true;
            _settings.ProActions.Bolts.Enabled = BoltsEnabled.IsChecked == true;
        }
        Save();
        RefreshProUi();
    }

    private void ProSpeed_Click(object sender, RoutedEventArgs e)
    {
        if (sender is not Button b || b.Tag?.ToString()?.Split('|') is not { Length: 2 } parts) return;
        var mode = parts[1] is "stable" or "fast" or "turbo" or "instant" ? parts[1] : "fast";
        if (parts[0] == "boltpush") _settings.ProActions.BoltPush.SpeedMode = mode;
        else _settings.ProActions.Bolts.SpeedMode = mode;
        Save();
        RefreshProUi();
    }

    private void BoltPushCoordinate_Changed(object sender, SelectionChangedEventArgs e)
    {
        if (_initializing) return;
        _settings.ProActions.BoltPush.CoordinateId = BoltPushCoordinate.SelectedItem is CoordinateItem c ? c.Id : "";
        Save();
    }

    private void TestProAction_Click(object sender, RoutedEventArgs e)
    {
        if (sender is Button b) _ = RunProActionAsync(b.Tag?.ToString() ?? "");
    }

    private void TriggerProHotkey(string key, bool remote)
    {
        var p = _settings.ProActions.BoltPush;
        var b = _settings.ProActions.Bolts;
        if (p.Enabled && string.Equals(p.Hotkey, key, StringComparison.OrdinalIgnoreCase))
        {
            _ = RunProActionAsync("boltpush");
            if (remote) Log($"Squad E/V → Bolt Push ({key})");
            return;
        }
        if (b.Enabled && string.Equals(b.Hotkey, key, StringComparison.OrdinalIgnoreCase))
        {
            _ = RunProActionAsync("bolts");
            if (remote) Log($"Squad E/V → Bolts ({key})");
        }
    }

    private async Task TapTripleVOrdered(ProTiming t, bool beforeShift)
    {
        // Never let the next Shift overtake the third V on very fast modes.
        // Explicit down/up pairs + a tiny barrier keep the game-facing order V,V,V -> Shift.
        var hold = Math.Max(2, t.KeyHold);
        var gap = Math.Max(2, t.StepGap);
        for (var i = 0; i < 3; i++)
        {
            InputService.KeyDown("V");
            await Delay(hold);
            InputService.KeyUp("V");
            if (i < 2) await Delay(gap);
        }
        InputService.KeyUp("V");
        if (beforeShift) await Delay(Math.Max(8, t.StepGap));
    }

    private async Task RunProActionAsync(string action)
    {
        if (action == "boltpush")
        {
            var s = _settings.ProActions.BoltPush;
            var coord = _settings.Coordinates.FirstOrDefault(c => c.Id == s.CoordinateId);
            if (coord?.X is not int x || coord.Y is not int y)
            {
                Log("Bolt Push error: no coordinate selected. Set a point in Coordinates first.");
                ShowPage("Macros");
                return;
            }
            if (!await _boltPushRun.WaitAsync(0)) return;
            try
            {
                var t = ProTiming.For(s.SpeedMode);
                BoltPushState.Text = "● RUNNING";
                InputService.MouseClick("right");
                await Delay(t.MouseGap);
                InputService.TapKey("SHIFT", t.ModifierHold, CancellationToken.None);
                await Delay(t.StepGap);

                // Critical order: all three V taps are fully completed BEFORE the second Shift.
                await TapTripleVOrdered(t, beforeShift: true);

                InputService.TapKey("SHIFT", t.ModifierHold, CancellationToken.None);
                InputService.KeyUp("V");
                InputService.KeyUp("SHIFT");
                // Instant still forces a real SHIFT-UP and a tiny safety gap before the coordinate click.
                await Delay(Math.Max(8, t.FinalSafety));
                InputService.SetCursor(x, y);
                await Delay(Math.Max(1, t.PointerSettle));
                InputService.MouseClick("left");
                Log($"Bolt Push · {s.SpeedMode.ToUpperInvariant()} · {x}, {y}");
            }
            finally
            {
                InputService.KeyUp("V");
                InputService.KeyUp("SHIFT");
                _boltPushRun.Release();
                RefreshProUi();
            }
        }
        else if (action == "bolts")
        {
            var s = _settings.ProActions.Bolts;
            if (!await _boltsRun.WaitAsync(0)) return;
            try
            {
                var t = ProTiming.For(s.SpeedMode);
                BoltsState.Text = "● RUNNING";
                await TapTripleVOrdered(t, beforeShift: false);
                Log($"Bolts · {s.SpeedMode.ToUpperInvariant()}");
            }
            finally
            {
                InputService.KeyUp("V");
                _boltsRun.Release();
                RefreshProUi();
            }
        }
    }

    private static Task Delay(int ms) => ms <= 0 ? Task.CompletedTask : Task.Delay(ms);

    private readonly record struct ProTiming(int KeyHold, int ModifierHold, int StepGap, int MouseGap, int PointerSettle, int FinalSafety)
    {
        public static ProTiming For(string mode) => mode switch
        {
            "stable" => new(24, 55, 24, 30, 35, 18),
            "turbo" => new(4, 10, 2, 4, 6, 8),
            "instant" => new(1, 5, 0, 1, 1, 8),
            _ => new(12, 28, 8, 12, 14, 10)
        };
    }

    private async void CreateSquad_Click(object sender, RoutedEventArgs e)
    {
        if (!int.TryParse(SquadPortBox.Text, out var port)) port = 42871;
        _settings.Squad.Port = Math.Clamp(port, 1024, 65535);
        _settings.Squad.DisplayName = string.IsNullOrWhiteSpace(SquadNameBox.Text) ? "Player" : SquadNameBox.Text.Trim();
        Save();
        try
        {
            SquadStatusText.Text = "Opening owner server...";
            var code = await _squad.HostAsync(_settings.Squad.Port, _settings.Squad.DisplayName);
            SquadCodeBox.Text = code;
            RefreshSquadUi();
        }
        catch (Exception ex) { Log("Squad: " + ex.Message); SquadStatusText.Text = ex.Message; }
    }

    private async void JoinSquad_Click(object sender, RoutedEventArgs e)
    {
        _settings.Squad.DisplayName = string.IsNullOrWhiteSpace(SquadNameBox.Text) ? "Player" : SquadNameBox.Text.Trim();
        Save();
        try
        {
            SquadStatusText.Text = "Connecting...";
            await _squad.JoinAsync(SquadCodeBox.Text, _settings.Squad.DisplayName);
            RefreshSquadUi();
        }
        catch (Exception ex) { Log("Squad: " + ex.Message); SquadStatusText.Text = ex.Message; }
    }

    private async void LeaveSquad_Click(object sender, RoutedEventArgs e)
    {
        await _squad.StopAsync();
        RefreshSquadUi();
    }

    private void CopySquadCode_Click(object sender, RoutedEventArgs e)
    {
        if (!string.IsNullOrWhiteSpace(SquadCodeBox.Text)) Clipboard.SetText(SquadCodeBox.Text.Trim());
    }

    private void RefreshSquadUi()
    {
        if (SquadStatusText is null) return;
        if (!_squad.IsConnected)
        {
            SquadRoleText.Text = "OFFLINE";
            SquadMembersText.Text = "No members";
            SquadCodeBox.IsReadOnly = false;
            SquadOwnerHint.Visibility = Visibility.Collapsed;
            return;
        }
        SquadRoleText.Text = _squad.IsHost ? "OWNER" : "MEMBER";
        SquadMembersText.Text = $"{_squad.MemberCount} connected · {_squad.MembersText}";
        SquadOwnerHint.Visibility = _squad.IsHost ? Visibility.Visible : Visibility.Collapsed;
        if (_squad.IsHost) SquadCodeBox.Text = _squad.JoinCode;
    }
}
