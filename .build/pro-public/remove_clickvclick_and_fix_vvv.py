from pathlib import Path
import re
root=Path("src")

# 1) Activation: close immediately after successful activation.
p=root/"PaidActivationWindow.xaml.cs"
if p.exists():
    s=p.read_text(encoding="utf-8")
    s=s.replace('        await Task.Delay(350); DialogResult=true; Close();',
                '        DialogResult=true; Close();')
    p.write_text(s,encoding="utf-8")

# 2) Remove CLICK VVV CLICK card from UI completely.
p=root/"MainWindow.xaml"
s=p.read_text(encoding="utf-8")
# remove the whole card containing ClickVClickEnabled
pat=r'\s*<Border Style="\{StaticResource CardBorder\}" Margin="0,12,0,0">(?:(?!</Border>).)*?ClickVClickEnabled(?:(?!</Border>).)*?</Border>'
ns,n=re.subn(pat,'',s,count=1,flags=re.S)
if n==0:
    # broader nested-border tolerant removal: from card start before CLICK VVV CLICK to next sibling card/end stack
    start=s.find('<Border Style="{StaticResource CardBorder}"', max(0,s.find('CLICK VVV CLICK')-1500))
    hit=s.find('CLICK VVV CLICK')
    if hit>=0 and start>=0 and start<hit:
        depth=0; pos=start
        while pos < len(s):
            o=s.find('<Border',pos); c=s.find('</Border>',pos)
            if c<0: break
            if o!=-1 and o<c:
                depth+=1; pos=o+7
            else:
                depth-=1; pos=c+9
                if depth==0:
                    s=s[:start]+s[pos:]
                    n=1; break
else:
    s=ns
p.write_text(s,encoding="utf-8")

# 3) Replace Bolts engine with only Bolt Push + Bolts and reliable VVV timings.
p=root/"MainWindow.Bolts.cs"
p.write_text(r'''using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;

namespace RiuClickerCS;

public partial class MainWindow
{
    private readonly SemaphoreSlim _boltPushRun = new(1, 1);
    private readonly SemaphoreSlim _boltsRun = new(1, 1);

    private void InitializeBoltsFeatures() => RefreshBoltsUi();

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
        Save(); RefreshBoltsUi();
    }

    private void BoltSpeed_Click(object sender, RoutedEventArgs e)
    {
        if (sender is not Button b || b.Tag?.ToString()?.Split('|') is not { Length: 2 } parts) return;
        var mode = parts[1] is "stable" or "fast" or "turbo" or "instant" ? parts[1] : "fast";
        if (parts[0] == "boltpush") _settings.Bolts.BoltPush.SpeedMode = mode;
        else _settings.Bolts.Bolts.SpeedMode = mode;
        Save(); RefreshBoltsUi();
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
        if (p.Enabled && string.Equals(p.Hotkey, key, StringComparison.OrdinalIgnoreCase)) _ = RunBoltActionAsync("boltpush");
        if (b.Enabled && string.Equals(b.Hotkey, key, StringComparison.OrdinalIgnoreCase)) _ = RunBoltActionAsync("bolts");
    }

    private async Task TapTripleVOrdered(BoltTiming t, bool beforeFinalShift)
    {
        var hold = Math.Max(3, t.KeyHold);
        var gap = Math.Max(2, t.StepGap);
        InputService.KeyUp("V");
        await BoltDelay(3);
        for (var i = 0; i < 3; i++)
        {
            InputService.KeyDown("V");
            await BoltDelay(hold);
            InputService.KeyUp("V");
            if (i < 2) await BoltDelay(gap);
        }
        InputService.KeyUp("V");
        if (beforeFinalShift) await BoltDelay(Math.Max(5, t.FinalBarrier));
    }

    private async Task RunBoltActionAsync(string action)
    {
        if (action == "boltpush")
        {
            var s = _settings.Bolts.BoltPush;
            var coord = _settings.Coordinates.FirstOrDefault(c => c.Id == s.CoordinateId);
            if (coord?.X is not int x || coord.Y is not int y) { Log("Bolt Push: select a coordinate first."); ShowPage("Macros"); return; }
            if (!await _boltPushRun.WaitAsync(0)) return;
            try
            {
                var t = BoltTiming.For(s.SpeedMode);
                BoltPushState.Text = "● RUNNING";
                InputService.TapKey("SHIFT", t.ModifierHold, CancellationToken.None);
                if (t.StepGap > 0) await BoltDelay(t.StepGap);
                await TapTripleVOrdered(t, true);
                InputService.TapKey("SHIFT", t.ModifierHold, CancellationToken.None);
                InputService.KeyUp("V"); InputService.KeyUp("SHIFT");
                await BoltDelay(t.FinalSafety);
                InputService.SetCursor(x, y);
                await BoltDelay(t.PointerSettle);
                InputService.MouseClickHeld("left", t.ClickHold, CancellationToken.None);
                await BoltDelay(t.AfterClick);
            }
            finally { InputService.KeyUp("V"); InputService.KeyUp("SHIFT"); _boltPushRun.Release(); RefreshBoltsUi(); }
        }
        else if (action == "bolts")
        {
            var s = _settings.Bolts.Bolts;
            if (!await _boltsRun.WaitAsync(0)) return;
            try { var t=BoltTiming.For(s.SpeedMode); BoltsState.Text="● RUNNING"; await TapTripleVOrdered(t,false); }
            finally { InputService.KeyUp("V"); _boltsRun.Release(); RefreshBoltsUi(); }
        }
    }

    private static Task BoltDelay(int ms) => ms <= 0 ? Task.CompletedTask : Task.Delay(ms);

    private readonly record struct BoltTiming(int KeyHold,int ModifierHold,int StepGap,int PointerSettle,int FinalBarrier,int FinalSafety,int ClickHold,int AfterClick)
    {
        public static BoltTiming For(string mode)=>mode switch
        {
            "stable" => new(24,50,22,28,16,18,16,8),
            "turbo" => new(5,10,3,8,6,12,14,6),
            "instant" => new(3,4,2,7,5,10,14,6),
            _ => new(10,24,7,10,8,10,14,6)
        };
    }
}
''',encoding="utf-8")

# 4) Remove ClickVClick from physical hotkey match/capture so old saved settings cannot trigger it.
p=root/"MainWindow.Extras.cs"
s=p.read_text(encoding="utf-8")
s=re.sub(r'\s*\|\|\s*\(_settings\.Bolts\.ClickVClick\.Enabled.*?\);',');',s,flags=re.S)
s=re.sub(r'\s*else if \(target == "clickvclick"\).*?;','',s)
p.write_text(s,encoding="utf-8")

# Safety validation
x=(root/"MainWindow.xaml").read_text(encoding="utf-8")
if "ClickVClickEnabled" in x or "CLICK VVV CLICK" in x:
    raise SystemExit("CLICK VVV CLICK UI still present")
print("cleanup applied: activation + VVV reliability + removed Click VVV Click")
