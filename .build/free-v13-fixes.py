from pathlib import Path
import re

root=Path("src")

# --- Remove the old Click VVV Click built-in if a previous patch chain added it. ---
p=root/"Models.cs"
s=p.read_text(encoding="utf-8")
s=re.sub(r'\n\s*public BoltMacroSettings ClickVClick \{ get; set; \} = new\(\) \{ Hotkey = "C" \};','',s)
s=re.sub(r'\n\s*s\.Bolts\.ClickVClick \?\?=.*?;','',s)
s=re.sub(r'\n\s*s\.Bolts\.ClickVClick\.SpeedMode = .*?;','',s)
p.write_text(s,encoding="utf-8")

p=root/"MainWindow.Extras.cs"
s=p.read_text(encoding="utf-8")
s=s.replace(' ||\n                          (_settings.Bolts.ClickVClick.Enabled && string.Equals(_settings.Bolts.ClickVClick.Hotkey, key, StringComparison.OrdinalIgnoreCase))','')
s=re.sub(r'\n\s*else if \(target == "clickvclick"\).*?;','',s)
p.write_text(s,encoding="utf-8")

p=root/"MainWindow.xaml"
s=p.read_text(encoding="utf-8")
# Remove CLICK VVV CLICK card if present.
hit=s.find('CLICK VVV CLICK')
if hit>=0:
    start=s.rfind('<Border Style="{StaticResource CardBorder}"',0,hit)
    if start>=0:
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
                    break
p.write_text(s,encoding="utf-8")

# --- Input helpers for a free-moving final Bolt Push click. ---
p=root/"InputService.cs"
s=p.read_text(encoding="utf-8")
if 'public static void MouseDown(string button)' not in s:
    marker='    public static void MouseClick(string button)\n'
    idx=s.find(marker)
    if idx<0: raise SystemExit("MouseClick marker missing")
    helper=r'''    public static void MouseDown(string button)
    {
        button = button.ToLowerInvariant();
        var (down, _, data) = button switch
        {
            "right" or "mouse2" => (0x0008u, 0x0010u, 0u),
            "middle" or "mouse3" => (0x0020u, 0x0040u, 0u),
            "x1" or "mouse4" => (0x0080u, 0x0100u, 1u),
            "x2" or "mouse5" => (0x0080u, 0x0100u, 2u),
            _ => (0x0002u, 0x0004u, 0u)
        };
        SendMouse(down, 0, 0, data);
    }

    public static void MouseUp(string button)
    {
        button = button.ToLowerInvariant();
        var (_, up, data) = button switch
        {
            "right" or "mouse2" => (0x0008u, 0x0010u, 0u),
            "middle" or "mouse3" => (0x0020u, 0x0040u, 0u),
            "x1" or "mouse4" => (0x0080u, 0x0100u, 1u),
            "x2" or "mouse5" => (0x0080u, 0x0100u, 2u),
            _ => (0x0002u, 0x0004u, 0u)
        };
        SendMouse(up, 0, 0, data);
    }

'''
    s=s[:idx]+helper+s[idx:]
p.write_text(s,encoding="utf-8")

# --- Bolt Push: reliable VVV + restore cursor immediately after final mouse-down. ---
p=root/"MainWindow.Bolts.cs"
s=p.read_text(encoding="utf-8")

s=re.sub(r'var hold = Math\.Max\([^;]+;', 'var hold = Math.Max(10, t.KeyHold);', s)
s=re.sub(r'var gap = Math\.Max\([^;]+;', 'var gap = Math.Max(14, t.StepGap);', s)

old='''                InputService.SetCursor(x, y);
                await BoltDelay(t.PointerSettle);

                // A held click is much more reliable than an immediate down/up pair in games,
                // especially on Turbo / Instant where the previous timings were only 3-5 ms.
                InputService.MouseClickHeld("left", t.ClickHold, CancellationToken.None);
                await BoltDelay(t.AfterClick);
'''
new='''                var returnPos = InputService.CursorPosition();
                InputService.SetCursor(x, y);
                await BoltDelay(t.PointerSettle);

                // Press at the saved coordinate, then immediately release control of the cursor.
                // The mouse can be moved while the final click is still held.
                InputService.MouseDown("left");
                InputService.SetCursor(returnPos.X, returnPos.Y);
                await BoltDelay(Math.Max(10, t.ClickHold));
                InputService.MouseUp("left");
                await BoltDelay(t.AfterClick);
'''
if old not in s:
    raise SystemExit("Bolt Push final click target missing")
s=s.replace(old,new,1)

s=s.replace('"turbo" => new(4, 10, 2, 8, 5, 12, 14, 6),','"turbo" => new(10, 12, 14, 8, 10, 12, 14, 6),')
s=s.replace('"instant" => new(1, 4, 0, 7, 3, 10, 14, 6),','"instant" => new(10, 10, 14, 7, 10, 10, 14, 6),')
s=s.replace('_ => new(10, 24, 7, 10, 8, 10, 14, 6)','_ => new(12, 24, 14, 10, 12, 10, 14, 6)')
p.write_text(s,encoding="utf-8")

# --- Persistent autoclicker: it runs until the user explicitly stops it. ---
p=root/"Engines.cs"
s=p.read_text(encoding="utf-8")
start=s.find("public sealed class ClickerEngine")
end=s.find("public sealed class MacroEngine")
if start<0 or end<0: raise SystemExit("ClickerEngine block missing")
clicker=r'''public sealed class ClickerEngine
{
    private CancellationTokenSource? _cts;
    private readonly Random _random = new();
    private volatile bool _desiredRunning;

    public bool Running { get; private set; }
    public long ClickCount { get; private set; }
    public DateTime? StartedAt { get; private set; }
    public event Action<bool>? RunningChanged;
    public event Action<long>? CountChanged;
    public event Action<string>? Message;

    public bool Start(ClickerSettings settings, Func<string, CoordinateItem?> resolver)
    {
        if (Running) return false;
        var snapshot = SettingsStore.CopyClicker(settings);
        _cts = new CancellationTokenSource();
        _desiredRunning = true;
        Running = true;
        ClickCount = 0;
        StartedAt = DateTime.Now;
        RunningChanged?.Invoke(true);
        _ = Task.Run(() => RunPersistent(snapshot, resolver, _cts.Token));
        return true;
    }

    public void Stop(string reason = "Остановлен")
    {
        _desiredRunning = false;
        try { _cts?.Cancel(); } catch { }
        if (Running) Message?.Invoke(reason);
    }

    public bool TestSingleClick(ClickerSettings settings, Func<string, CoordinateItem?> resolver)
        => PerformClick(SettingsStore.CopyClicker(settings), resolver);

    private async Task RunPersistent(ClickerSettings settings, Func<string, CoordinateItem?> resolver, CancellationToken token)
    {
        try
        {
            if (settings.StartDelayMs > 0) await Task.Delay(settings.StartDelayMs, token);
            var next = Stopwatch.GetTimestamp();
            while (_desiredRunning && !token.IsCancellationRequested)
            {
                if (settings.ClickLimit > 0 && ClickCount >= settings.ClickLimit)
                {
                    _desiredRunning = false;
                    break;
                }

                try
                {
                    if (!PerformClick(settings, resolver))
                    {
                        await Task.Delay(50, token);
                        continue;
                    }
                    ClickCount++;
                    if (ClickCount % 5 == 0) CountChanged?.Invoke(ClickCount);
                }
                catch (OperationCanceledException) { throw; }
                catch (Exception ex)
                {
                    Message?.Invoke("Кликер продолжил работу после ошибки: " + ex.Message);
                    await Task.Delay(25, token);
                }

                var cps = double.IsFinite(settings.Cps) && settings.Cps > 0 ? settings.Cps : 12;
                var periodMs = 1000.0 / cps;
                if (settings.Humanize && settings.JitterPercent > 0)
                {
                    var span = periodMs * settings.JitterPercent / 100.0;
                    periodMs += (_random.NextDouble() * 2 - 1) * span;
                }
                next += (long)Math.Max(1, periodMs * Stopwatch.Frequency / 1000.0);
                await WaitUntil(next, token);
            }
        }
        catch (OperationCanceledException) { }
        finally
        {
            Running = false;
            _desiredRunning = false;
            CountChanged?.Invoke(ClickCount);
            RunningChanged?.Invoke(false);
        }
    }

    private static bool PerformClick(ClickerSettings s, Func<string, CoordinateItem?> resolver)
    {
        if (s.ClickMode == "coordinate")
        {
            var c = resolver(s.SelectedCoordinateId);
            if (c?.X is not int x || c.Y is not int y) return false;
            var old = InputService.CursorPosition();
            InputService.SetCursor(x, y);
            try { InputService.MouseClick(s.MouseButton); }
            finally { InputService.SetCursor(old.X, old.Y); }
            return true;
        }
        InputService.MouseClick(s.MouseButton);
        return true;
    }

    private static async Task WaitUntil(long target, CancellationToken token)
    {
        while (true)
        {
            token.ThrowIfCancellationRequested();
            var remaining = target - Stopwatch.GetTimestamp();
            if (remaining <= 0) return;
            var ms = remaining * 1000.0 / Stopwatch.Frequency;
            if (ms >= 3)
            {
                await Task.Delay(Math.Max(1, (int)Math.Floor(ms - 1)), token);
                continue;
            }
            var spinner = new SpinWait();
            while (Stopwatch.GetTimestamp() < target)
            {
                token.ThrowIfCancellationRequested();
                spinner.SpinOnce();
            }
            return;
        }
    }
}

'''
s=s[:start]+clicker+s[end:]
p.write_text(s,encoding="utf-8")

# --- Three selectable interfaces on startup. ---
# Add names needed for runtime layout switching.
p=root/"MainWindow.xaml"
s=p.read_text(encoding="utf-8")
s=s.replace('<ColumnDefinition Width="232"/><ColumnDefinition Width="*"/>',
            '<ColumnDefinition x:Name="SidebarColumn" Width="232"/><ColumnDefinition Width="*"/>',1)
s=s.replace('<Grid Grid.Column="1" Margin="24,18,24,20">',
            '<Grid x:Name="MainContentArea" Grid.Column="1" Margin="24,18,24,20">',1)
p.write_text(s,encoding="utf-8")

(root/"InterfacePickerWindow.xaml").write_text(r'''<Window x:Class="RiuClickerCS.InterfacePickerWindow"
 xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
 xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
 Title="RiuClicker · Interface" Width="660" Height="390"
 WindowStartupLocation="CenterScreen" ResizeMode="NoResize" Background="#080B12" Foreground="White">
 <Grid Margin="26">
  <Grid.RowDefinitions><RowDefinition Height="Auto"/><RowDefinition Height="*"/><RowDefinition Height="Auto"/></Grid.RowDefinitions>
  <StackPanel>
   <TextBlock Text="RIUCLICKER" Foreground="#22D3EE" FontWeight="Bold"/>
   <TextBlock Text="CHOOSE INTERFACE" FontSize="30" FontWeight="Black" Margin="0,6,0,4"/>
   <TextBlock Text="You can choose a different look every launch." Foreground="#94A3B8"/>
  </StackPanel>
  <UniformGrid Grid.Row="1" Columns="3" Margin="0,22,0,18">
   <Button Content="CLASSIC&#10;&#10;Original balanced layout" Tag="classic" Margin="5" Padding="12" Click="Pick_Click"/>
   <Button Content="COMPACT&#10;&#10;Smaller sidebar and tighter cards" Tag="compact" Margin="5" Padding="12" Click="Pick_Click"/>
   <Button Content="NEON&#10;&#10;Wide layout with purple accent" Tag="neon" Margin="5" Padding="12" Click="Pick_Click"/>
  </UniformGrid>
  <TextBlock Grid.Row="2" Text="Select one to continue" Foreground="#64748B" HorizontalAlignment="Center"/>
 </Grid>
</Window>''',encoding="utf-8")

(root/"InterfacePickerWindow.xaml.cs").write_text(r'''using System.Windows;
namespace RiuClickerCS;
public partial class InterfacePickerWindow : Window
{
    public string SelectedMode { get; private set; } = "classic";
    public InterfacePickerWindow() { InitializeComponent(); }
    private void Pick_Click(object sender, RoutedEventArgs e)
    {
        if (sender is FrameworkElement f && f.Tag is string mode) SelectedMode = mode;
        DialogResult = true;
        Close();
    }
}
''',encoding="utf-8")

(root/"UiModeService.cs").write_text(r'''using System.Windows;
using System.Windows.Media;
namespace RiuClickerCS;
public static class UiModeService
{
    public static void Apply(MainWindow w, string mode)
    {
        mode = (mode ?? "classic").ToLowerInvariant();
        if (mode == "compact")
        {
            w.SidebarColumn.Width = new GridLength(184);
            w.MainContentArea.Margin = new Thickness(16, 14, 16, 16);
            Application.Current.Resources["AccentBrush"] = new SolidColorBrush(Color.FromRgb(34, 211, 238));
            Application.Current.Resources["CardBrush"] = new SolidColorBrush(Color.FromRgb(12, 17, 25));
            Application.Current.Resources["SidebarBrush"] = new SolidColorBrush(Color.FromRgb(7, 10, 15));
        }
        else if (mode == "neon")
        {
            w.SidebarColumn.Width = new GridLength(248);
            w.MainContentArea.Margin = new Thickness(30, 22, 30, 24);
            Application.Current.Resources["AccentBrush"] = new SolidColorBrush(Color.FromRgb(168, 85, 247));
            Application.Current.Resources["CardBrush"] = new SolidColorBrush(Color.FromRgb(19, 14, 30));
            Application.Current.Resources["SidebarBrush"] = new SolidColorBrush(Color.FromRgb(10, 7, 18));
        }
        else
        {
            w.SidebarColumn.Width = new GridLength(232);
            w.MainContentArea.Margin = new Thickness(24, 18, 24, 20);
        }
    }
}
''',encoding="utf-8")

# Insert picker immediately before the main window opens.
p=root/"App.xaml.cs"
s=p.read_text(encoding="utf-8")
old='''    private void OpenMainWindow()
    {
        var main = new MainWindow();
        MainWindow = main;
        ShutdownMode = ShutdownMode.OnMainWindowClose;
        main.Show();
    }
'''
new='''    private void OpenMainWindow()
    {
        var picker = new InterfacePickerWindow();
        var mode = picker.ShowDialog() == true ? picker.SelectedMode : "classic";
        var main = new MainWindow();
        UiModeService.Apply(main, mode);
        MainWindow = main;
        ShutdownMode = ShutdownMode.OnMainWindowClose;
        main.Show();
    }
'''
if old not in s: raise SystemExit("OpenMainWindow target missing")
s=s.replace(old,new,1)
p.write_text(s,encoding="utf-8")

# Version 1.3.
p=root/"RiuClickerCS.csproj"
s=p.read_text(encoding="utf-8")
s=re.sub(r'<Version>[^<]+</Version>','<Version>1.3.0</Version>',s)
s=re.sub(r'<FileVersion>[^<]+</FileVersion>','<FileVersion>1.3.0.0</FileVersion>',s)
s=re.sub(r'<AssemblyVersion>[^<]+</AssemblyVersion>','<AssemblyVersion>1.3.0.0</AssemblyVersion>',s)
p.write_text(s,encoding="utf-8")

for name in ["MainWindow.xaml","MainWindow.xaml.cs","MainWindow.Extras.cs","BrandVisual.cs","ActivationWindow.xaml"]:
    p=root/name
    if p.exists():
        t=p.read_text(encoding="utf-8").replace("RiuClicker 1.2","RiuClicker 1.3").replace("RIUCLICKER 1.2","RIUCLICKER 1.3")
        p.write_text(t,encoding="utf-8")

print("RiuClicker 1.3 fixes applied")
