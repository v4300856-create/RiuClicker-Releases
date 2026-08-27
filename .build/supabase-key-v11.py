from pathlib import Path

root = Path('src')
endpoint = 'https://rpbjeexhbanaavazfmpo.supabase.co/functions/v1/riu-license'
loot = 'https://loot-link.com/s?Uo5NePL7'

(root / 'LicenseService.cs').write_text(r'''using Microsoft.Win32;
using System.IO;
using System.Net.Http;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;

namespace RiuClickerCS;

public sealed class LicenseResult
{
    public bool Ok { get; set; }
    public bool Pending { get; set; }
    public string Key { get; set; } = "";
    public string Message { get; set; } = "";
    public string Plan { get; set; } = "";
    public DateTimeOffset? ExpiresAt { get; set; }
}

public static class LicenseService
{
    public const string Endpoint = "https://rpbjeexhbanaavazfmpo.supabase.co/functions/v1/riu-license";
    public const string LootLabsUrl = "https://loot-link.com/s?Uo5NePL7";
    private static readonly HttpClient Http = new() { Timeout = TimeSpan.FromSeconds(10) };
    private static readonly string Folder = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData), "RiuClicker");
    private static readonly string LicenseFile = Path.Combine(Folder, "license.json");

    public static string DeviceId()
    {
        var machineGuid = "";
        try
        {
            using var key = Registry.LocalMachine.OpenSubKey(@"SOFTWARE\Microsoft\Cryptography");
            machineGuid = key?.GetValue("MachineGuid")?.ToString() ?? "";
        }
        catch { }
        var raw = string.Join("|", machineGuid, Environment.MachineName, Environment.ProcessorCount, Environment.OSVersion.VersionString);
        return Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(raw)))[..24];
    }

    public static string CreateSessionId()
    {
        var bytes = RandomNumberGenerator.GetBytes(24);
        return Convert.ToHexString(bytes);
    }

    public static string GetKeyStartUrl(string sessionId) => Endpoint + "/start?deviceId=" + Uri.EscapeDataString(DeviceId()) + "&sessionId=" + Uri.EscapeDataString(sessionId);

    public static string? LoadSavedKey()
    {
        try
        {
            if (!File.Exists(LicenseFile)) return null;
            using var doc = JsonDocument.Parse(File.ReadAllText(LicenseFile));
            return doc.RootElement.TryGetProperty("key", out var k) ? k.GetString() : null;
        }
        catch { return null; }
    }

    public static void SaveKey(string key)
    {
        Directory.CreateDirectory(Folder);
        File.WriteAllText(LicenseFile, JsonSerializer.Serialize(new { key = Normalize(key) }));
    }

    public static void ClearSavedKey()
    {
        try { if (File.Exists(LicenseFile)) File.Delete(LicenseFile); } catch { }
    }

    public static Task<LicenseResult> ActivateAsync(string key, CancellationToken ct = default) => SendAsync(new { action = "activate", key = Normalize(key), deviceId = DeviceId() }, ct);
    public static Task<LicenseResult> ValidateAsync(string key, CancellationToken ct = default) => SendAsync(new { action = "validate", key = Normalize(key), deviceId = DeviceId() }, ct);
    public static Task<LicenseResult> PollAsync(string sessionId, CancellationToken ct = default) => SendAsync(new { action = "poll", sessionId, deviceId = DeviceId() }, ct);

    private static async Task<LicenseResult> SendAsync(object payload, CancellationToken ct)
    {
        try
        {
            var json = JsonSerializer.Serialize(payload);
            using var req = new HttpRequestMessage(HttpMethod.Post, Endpoint) { Content = new StringContent(json, Encoding.UTF8, "application/json") };
            using var res = await Http.SendAsync(req, ct);
            var body = await res.Content.ReadAsStringAsync(ct);
            using var doc = JsonDocument.Parse(body);
            var r = doc.RootElement;
            var result = new LicenseResult
            {
                Ok = r.TryGetProperty("ok", out var ok) && ok.GetBoolean(),
                Pending = r.TryGetProperty("pending", out var pending) && pending.GetBoolean(),
                Key = r.TryGetProperty("key", out var key) ? key.GetString() ?? "" : "",
                Message = r.TryGetProperty("message", out var msg) ? msg.GetString() ?? "" : "",
                Plan = r.TryGetProperty("plan", out var plan) ? plan.GetString() ?? "" : ""
            };
            if (r.TryGetProperty("expiresAt", out var exp) && exp.ValueKind == JsonValueKind.String && DateTimeOffset.TryParse(exp.GetString(), out var dt)) result.ExpiresAt = dt;
            return result;
        }
        catch (TaskCanceledException) { return new() { Ok = false, Message = "Server timeout." }; }
        catch { return new() { Ok = false, Message = "Could not connect to key server." }; }
    }

    private static string Normalize(string key) => key.Trim().ToUpperInvariant().Replace(" ", "");
}
''', encoding='utf-8')

(root / 'ActivationWindow.xaml').write_text(r'''<Window x:Class="RiuClickerCS.ActivationWindow"
        xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
        xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
        Title="RiuClicker 1.1 · Key System" Width="560" Height="470"
        WindowStartupLocation="CenterScreen" ResizeMode="NoResize" Background="#080B12" Foreground="White">
    <Grid Margin="32">
        <Grid.RowDefinitions><RowDefinition Height="Auto"/><RowDefinition Height="*"/><RowDefinition Height="Auto"/></Grid.RowDefinitions>
        <StackPanel>
            <TextBlock Text="RIUCLICKER · KEY SYSTEM" Foreground="#A78BFA" FontSize="12" FontWeight="Bold"/>
            <TextBlock Text="Activate RiuClicker" FontSize="32" FontWeight="Bold" Margin="0,8,0,6"/>
            <TextBlock Text="Get a 24-hour key through LootLabs. The key is bound to this PC and expires automatically." Foreground="#94A3B8" FontSize="14" TextWrapping="Wrap"/>
        </StackPanel>

        <Border Grid.Row="1" Margin="0,24,0,18" Padding="22" CornerRadius="20" Background="#111827" BorderBrush="#293249" BorderThickness="1">
            <StackPanel VerticalAlignment="Center">
                <TextBlock Text="LICENSE KEY" Foreground="#94A3B8" FontSize="11" FontWeight="Bold"/>
                <TextBox x:Name="KeyBox" Height="48" Margin="0,8,0,12" FontFamily="Consolas" FontSize="17" CharacterCasing="Upper" VerticalContentAlignment="Center"/>
                <Grid>
                    <Grid.ColumnDefinitions><ColumnDefinition/><ColumnDefinition/></Grid.ColumnDefinitions>
                    <Button x:Name="GetKeyButton" Grid.Column="0" Content="GET KEY" Height="46" Margin="0,0,6,0" Click="GetKey_Click" Background="#171E2E" BorderBrush="#475569" Foreground="White" FontWeight="Bold"/>
                    <Button x:Name="ActivateButton" Grid.Column="1" Content="APPLY KEY" Height="46" Margin="6,0,0,0" Click="Activate_Click" Background="#7C3AED" BorderBrush="#8B5CF6" Foreground="White" FontWeight="Bold"/>
                </Grid>
                <TextBlock x:Name="StatusText" Margin="0,14,0,0" Foreground="#94A3B8" Text="Press GET KEY to start." TextWrapping="Wrap" TextAlignment="Center"/>
            </StackPanel>
        </Border>

        <Grid Grid.Row="2"><Grid.ColumnDefinitions><ColumnDefinition/><ColumnDefinition/></Grid.ColumnDefinitions>
            <TextBlock Text="24H · DEVICE BOUND" Foreground="#64748B" FontSize="11"/>
            <TextBlock x:Name="DeviceText" Grid.Column="1" Foreground="#64748B" FontFamily="Consolas" HorizontalAlignment="Right" FontSize="11"/>
        </Grid>
    </Grid>
</Window>
''', encoding='utf-8')

(root / 'ActivationWindow.xaml.cs').write_text(r'''using System.Diagnostics;
using System.Windows;
using System.Windows.Threading;

namespace RiuClickerCS;

public partial class ActivationWindow : Window
{
    public bool LicenseActivated { get; private set; }
    private string? _sessionId;
    private readonly DispatcherTimer _pollTimer = new() { Interval = TimeSpan.FromSeconds(2) };
    private int _pollCount;

    public ActivationWindow()
    {
        InitializeComponent();
        DeviceText.Text = LicenseService.DeviceId();
        _pollTimer.Tick += PollTimer_Tick;
        Closed += (_, __) => _pollTimer.Stop();
    }

    private void GetKey_Click(object sender, RoutedEventArgs e)
    {
        _sessionId = LicenseService.CreateSessionId();
        _pollCount = 0;
        var url = LicenseService.GetKeyStartUrl(_sessionId);
        try
        {
            Process.Start(new ProcessStartInfo(url) { UseShellExecute = true });
            StatusText.Text = "LootLabs opened · finish the tasks. Your key will appear here automatically.";
            GetKeyButton.IsEnabled = false;
            _pollTimer.Start();
        }
        catch
        {
            StatusText.Text = "Could not open LootLabs.";
            GetKeyButton.IsEnabled = true;
        }
    }

    private async void PollTimer_Tick(object? sender, EventArgs e)
    {
        if (string.IsNullOrWhiteSpace(_sessionId)) return;
        _pollCount++;
        if (_pollCount > 450)
        {
            _pollTimer.Stop();
            GetKeyButton.IsEnabled = true;
            StatusText.Text = "Key session expired · press GET KEY again.";
            return;
        }
        var result = await LicenseService.PollAsync(_sessionId);
        if (!result.Ok || result.Pending || string.IsNullOrWhiteSpace(result.Key)) return;
        _pollTimer.Stop();
        KeyBox.Text = result.Key;
        StatusText.Text = "Key received automatically · applying...";
        await ApplyCurrentKeyAsync();
    }

    private async void Activate_Click(object sender, RoutedEventArgs e) => await ApplyCurrentKeyAsync();

    private async Task ApplyCurrentKeyAsync()
    {
        var key = KeyBox.Text.Trim();
        if (string.IsNullOrWhiteSpace(key)) { StatusText.Text = "Enter a key or press GET KEY."; return; }
        ActivateButton.IsEnabled = false;
        StatusText.Text = "Checking key...";
        var result = await LicenseService.ActivateAsync(key);
        ActivateButton.IsEnabled = true;
        if (!result.Ok)
        {
            StatusText.Text = string.IsNullOrWhiteSpace(result.Message) ? "Key rejected." : result.Message;
            return;
        }
        LicenseService.SaveKey(key);
        LicenseActivated = true;
        StatusText.Text = result.ExpiresAt is { } exp ? $"ACTIVE · expires {exp.LocalDateTime:g}" : "ACTIVE · 24H";
        await Task.Delay(500);
        DialogResult = true;
        Close();
    }
}
''', encoding='utf-8')

print('Applied Supabase/LootLabs 24H key system UI and automatic polling')
