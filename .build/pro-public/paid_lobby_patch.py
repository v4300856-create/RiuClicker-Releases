from pathlib import Path
import re

root=Path("src")

def read(name):
    p=root/name
    return p,p.read_text(encoding="utf-8")

# Paid license service
(root/"PaidLicenseService.cs").write_text(r'''using Microsoft.Win32;
using System.IO;
using System.Net.Http;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;

namespace RiuClickerCS;

public sealed class PaidLicenseResult
{
    public bool Ok { get; set; }
    public string Error { get; set; } = "";
    public string Plan { get; set; } = "";
    public DateTimeOffset? ExpiresAt { get; set; }
}

public static class PaidLicenseService
{
    public const string Endpoint = "https://rpbjeexhbanaavazfmpo.supabase.co/functions/v1/riu-pro-license";
    private static readonly HttpClient Http = new() { Timeout = TimeSpan.FromSeconds(12) };
    private static readonly string Folder = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData), "RiuClickerPro");
    private static readonly string FilePath = Path.Combine(Folder, "paid-license.txt");

    public static string DeviceId()
    {
        var machineGuid = "";
        try
        {
            using var k = Registry.LocalMachine.OpenSubKey(@"SOFTWARE\\Microsoft\\Cryptography");
            machineGuid = k?.GetValue("MachineGuid")?.ToString() ?? "";
        }
        catch { }
        var raw = string.Join("|", machineGuid, Environment.MachineName, Environment.ProcessorCount);
        return Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(raw)))[..24];
    }

    public static string LoadKey()
    {
        try { return File.Exists(FilePath) ? File.ReadAllText(FilePath).Trim() : ""; }
        catch { return ""; }
    }

    public static void SaveKey(string key)
    {
        Directory.CreateDirectory(Folder);
        File.WriteAllText(FilePath, Normalize(key));
    }

    public static void ClearKey()
    {
        try { if (File.Exists(FilePath)) File.Delete(FilePath); } catch { }
    }

    public static Task<PaidLicenseResult> ActivateAsync(string key) => Send("activate", key);
    public static Task<PaidLicenseResult> ValidateAsync(string key) => Send("validate", key);

    private static async Task<PaidLicenseResult> Send(string action, string key)
    {
        try
        {
            var payload = JsonSerializer.Serialize(new { key = Normalize(key), hwid = DeviceId() });
            using var req = new HttpRequestMessage(HttpMethod.Post, Endpoint + "?action=" + action)
            {
                Content = new StringContent(payload, Encoding.UTF8, "application/json")
            };
            using var res = await Http.SendAsync(req);
            var body = await res.Content.ReadAsStringAsync();
            using var doc = JsonDocument.Parse(body);
            var r = doc.RootElement;
            if (!res.IsSuccessStatusCode || !r.TryGetProperty("ok", out var ok) || !ok.GetBoolean())
                return new() { Ok = false, Error = r.TryGetProperty("error", out var e) ? e.GetString() ?? "invalid_key" : "invalid_key" };

            var result = new PaidLicenseResult
            {
                Ok = true,
                Plan = r.TryGetProperty("plan", out var p) ? p.GetString() ?? "PRO" : "PRO"
            };
            if (r.TryGetProperty("expires_at", out var x) && x.ValueKind == JsonValueKind.String &&
                DateTimeOffset.TryParse(x.GetString(), out var dt))
                result.ExpiresAt = dt;
            return result;
        }
        catch { return new() { Ok = false, Error = "server_unavailable" }; }
    }

    static string Normalize(string key) => key.Trim().ToUpperInvariant().Replace(" ", "");
}
''',encoding="utf-8")

(root/"PaidActivationWindow.xaml").write_text(r'''<Window x:Class="RiuClickerCS.PaidActivationWindow"
 xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
 xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
 Title="RiuClicker PRO · Activation" Width="560" Height="400"
 WindowStartupLocation="CenterScreen" ResizeMode="NoResize" Background="#080B12" Foreground="White">
 <Grid Margin="30">
  <Grid.RowDefinitions><RowDefinition Height="Auto"/><RowDefinition Height="*"/><RowDefinition Height="Auto"/></Grid.RowDefinitions>
  <StackPanel>
   <TextBlock Text="RIUCLICKER · PAID" Foreground="#22D3EE" FontWeight="Bold"/>
   <TextBlock Text="PRO ACTIVATION" FontSize="30" FontWeight="Black" Margin="0,8,0,5"/>
   <TextBlock Text="Enter your paid RiuClicker key." Foreground="#94A3B8"/>
  </StackPanel>
  <Border Grid.Row="1" Background="#111827" BorderBrush="#293249" BorderThickness="1" CornerRadius="18" Padding="20" Margin="0,22,0,16">
   <StackPanel VerticalAlignment="Center">
    <TextBlock Text="LICENSE KEY" Foreground="#94A3B8" FontSize="10" FontWeight="Bold"/>
    <TextBox x:Name="KeyBox" Height="45" Margin="0,7,0,12" FontFamily="Consolas" FontSize="16" CharacterCasing="Upper"/>
    <Button x:Name="ActivateButton" Content="ACTIVATE" Height="45" Click="Activate_Click" Background="#7C3AED" Foreground="White" FontWeight="Bold"/>
    <TextBlock x:Name="StatusText" Text="30 / 90 days or Lifetime" Foreground="#94A3B8" TextAlignment="Center" Margin="0,12,0,0"/>
   </StackPanel>
  </Border>
  <TextBlock Grid.Row="2" x:Name="DeviceText" Foreground="#64748B" FontFamily="Consolas"/>
 </Grid>
</Window>''',encoding="utf-8")

(root/"PaidActivationWindow.xaml.cs").write_text(r'''using System.Windows;
namespace RiuClickerCS;
public partial class PaidActivationWindow : Window
{
    public bool Activated { get; private set; }
    public PaidActivationWindow()
    {
        InitializeComponent();
        DeviceText.Text = "DEVICE · " + PaidLicenseService.DeviceId();
        KeyBox.Text = PaidLicenseService.LoadKey();
    }
    private async void Activate_Click(object sender, RoutedEventArgs e)
    {
        var key=KeyBox.Text.Trim();
        if(string.IsNullOrWhiteSpace(key)) return;
        ActivateButton.IsEnabled=false; StatusText.Text="CHECKING...";
        var result=await PaidLicenseService.ActivateAsync(key);
        ActivateButton.IsEnabled=true;
        if(!result.Ok){StatusText.Text="REJECTED · "+result.Error;return;}
        PaidLicenseService.SaveKey(key); Activated=true;
        StatusText.Text=result.ExpiresAt is { } exp ? $"ACTIVE · {result.Plan} · {exp.LocalDateTime:g}" : $"ACTIVE · {result.Plan}";
        await Task.Delay(350); DialogResult=true; Close();
    }
}
''',encoding="utf-8")

# App paid gate
(root/"App.xaml").write_text(r'''<Application x:Class="RiuClickerCS.App"
 xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
 xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml">
 <Application.Resources/>
</Application>''',encoding="utf-8")

(root/"App.xaml.cs").write_text(r'''using System.Windows;
namespace RiuClickerCS;
public partial class App : Application
{
    protected override async void OnStartup(StartupEventArgs e)
    {
        base.OnStartup(e);
        ShutdownMode=ShutdownMode.OnExplicitShutdown;
        var key=PaidLicenseService.LoadKey();
        if(!string.IsNullOrWhiteSpace(key))
        {
            var check=await PaidLicenseService.ValidateAsync(key);
            if(check.Ok){OpenMain();return;}
            PaidLicenseService.ClearKey();
        }
        var a=new PaidActivationWindow();
        if(a.ShowDialog()!=true || !a.Activated){Shutdown();return;}
        OpenMain();
    }
    private void OpenMain()
    {
        var main=new MainWindow();
        MainWindow=main;
        ShutdownMode=ShutdownMode.OnMainWindowClose;
        main.Show();
    }
}
''',encoding="utf-8")

# Lobby HTTP client
(root/"LobbyService.cs").write_text(r'''using System.Net.Http;
using System.Text;
using System.Text.Json;
namespace RiuClickerCS;
public sealed class LobbyEventItem { public long Id { get; set; } public string Action { get; set; }=""; }
public sealed class LobbyService
{
    const string Endpoint="https://rpbjeexhbanaavazfmpo.supabase.co/functions/v1/riu-pro-lobby";
    readonly HttpClient _http=new(){Timeout=TimeSpan.FromSeconds(10)};
    async Task<JsonDocument?> Call(object payload)
    {
        try
        {
            using var req=new HttpRequestMessage(HttpMethod.Post,Endpoint){Content=new StringContent(JsonSerializer.Serialize(payload),Encoding.UTF8,"application/json")};
            using var res=await _http.SendAsync(req);
            var txt=await res.Content.ReadAsStringAsync();
            if(!res.IsSuccessStatusCode)return null;
            return JsonDocument.Parse(txt);
        } catch { return null; }
    }
    object Base(string action,string code="")=>new{action,code,key=PaidLicenseService.LoadKey(),hwid=PaidLicenseService.DeviceId()};
    public async Task<(bool ok,string code,string ownerToken)> Create()
    {
        using var d=await Call(Base("create")); if(d is null)return(false,"","");
        var r=d.RootElement; return(r.GetProperty("ok").GetBoolean(),r.GetProperty("code").GetString()??"",r.GetProperty("owner_token").GetString()??"");
    }
    public async Task<(bool ok,long lastId)> Join(string code)
    {
        using var d=await Call(Base("join",code)); if(d is null)return(false,0);
        var r=d.RootElement; return(r.GetProperty("ok").GetBoolean(),r.TryGetProperty("last_id",out var i)?i.GetInt64():0);
    }
    public async Task<bool> Push(string code,string ownerToken,string ev)
    {
        using var d=await Call(new{action="push",code,owner_token=ownerToken,event=ev,key=PaidLicenseService.LoadKey(),hwid=PaidLicenseService.DeviceId()});
        return d is not null && d.RootElement.TryGetProperty("ok",out var ok)&&ok.GetBoolean();
    }
    public async Task<List<LobbyEventItem>> Poll(string code,long afterId)
    {
        using var d=await Call(new{action="poll",code,after_id=afterId,key=PaidLicenseService.LoadKey(),hwid=PaidLicenseService.DeviceId()});
        var list=new List<LobbyEventItem>(); if(d is null)return list;
        foreach(var e in d.RootElement.GetProperty("events").EnumerateArray())
            list.Add(new(){Id=e.GetProperty("id").GetInt64(),Action=e.GetProperty("action").GetString()??""});
        return list;
    }
}
''',encoding="utf-8")

(root/"MainWindow.Lobby.cs").write_text(r'''using System.Windows;
namespace RiuClickerCS;
public partial class MainWindow
{
    readonly LobbyService _lobby=new();
    CancellationTokenSource? _lobbyPollCts;
    string _lobbyCode="",_lobbyOwnerToken="";
    long _lobbyLastId;
    bool _lobbyOwner;

    private async void CreateLobby_Click(object sender,RoutedEventArgs e)
    {
        LeaveLobby(); LobbyStatusText.Text="CREATING...";
        var r=await _lobby.Create();
        if(!r.ok){LobbyStatusText.Text="CREATE FAILED";return;}
        _lobbyCode=r.code;_lobbyOwnerToken=r.ownerToken;_lobbyOwner=true;_lobbyLastId=0;
        LobbyCodeBox.Text=r.code;LobbyStatusText.Text="OWNER · ONLINE";StartLobbyPoll();
    }
    private async void JoinLobby_Click(object sender,RoutedEventArgs e)
    {
        LeaveLobby();var code=LobbyCodeBox.Text.Trim().ToUpperInvariant();LobbyStatusText.Text="JOINING...";
        var r=await _lobby.Join(code);
        if(!r.ok){LobbyStatusText.Text="LOBBY NOT FOUND";return;}
        _lobbyCode=code;_lobbyOwner=false;_lobbyLastId=r.lastId;LobbyStatusText.Text="MEMBER · ONLINE";StartLobbyPoll();
    }
    private void LeaveLobby_Click(object sender,RoutedEventArgs e)=>LeaveLobby();
    private void LeaveLobby()
    {
        _lobbyPollCts?.Cancel();_lobbyPollCts=null;_lobbyCode="";_lobbyOwnerToken="";_lobbyOwner=false;_lobbyLastId=0;
        if(LobbyStatusText is not null)LobbyStatusText.Text="OFFLINE";
    }
    private void StartLobbyPoll(){_lobbyPollCts=new();_=LobbyPollLoop(_lobbyPollCts.Token);}
    private async Task LobbyPollLoop(CancellationToken token)
    {
        while(!token.IsCancellationRequested&&!string.IsNullOrWhiteSpace(_lobbyCode))
        {
            var events=await _lobby.Poll(_lobbyCode,_lobbyLastId);
            foreach(var ev in events)
            {
                _lobbyLastId=Math.Max(_lobbyLastId,ev.Id);
                if(!_lobbyOwner&&(ev.Action=="E"||ev.Action=="V"))
                    InputService.TapKey(ev.Action,10,CancellationToken.None);
            }
            try{await Task.Delay(140,token);}catch{break;}
        }
    }
    private void BroadcastPhysicalLobbyKey(string key)
    {
        if(!_lobbyOwner||string.IsNullOrWhiteSpace(_lobbyCode))return;
        if(key!="E"&&key!="V")return;
        _=_lobby.Push(_lobbyCode,_lobbyOwnerToken,key);
    }
}
''',encoding="utf-8")

# Add lobby navigation and page to XAML.
p,s=read("MainWindow.xaml")
nav='<Button Content="◆   Макросы" Tag="Macros" Style="{StaticResource NavButton}" Click="Nav_Click"/>'
if nav in s and 'Tag="Lobby"' not in s:
    s=s.replace(nav,nav+'\n                            <Button Content="◉   Lobby" Tag="Lobby" Style="{StaticResource NavButton}" Click="Nav_Click"/>',1)

marker='                        <!-- PROFILES PAGE -->'
lobby=r'''                        <!-- LOBBY PAGE -->
                        <ScrollViewer x:Name="PageLobby" Visibility="Collapsed" VerticalScrollBarVisibility="Auto">
                          <StackPanel>
                            <Border Style="{StaticResource HeroBorder}" Margin="0,0,0,12">
                              <StackPanel>
                                <TextBlock Text="RIU LOBBY" FontSize="22" FontWeight="Black" Foreground="{DynamicResource AccentBrush}"/>
                                <TextBlock Text="Owner physical E / V are repeated for members. Macro-generated V is not broadcast." Foreground="{DynamicResource MutedBrush}" Margin="0,6,0,0" TextWrapping="Wrap"/>
                              </StackPanel>
                            </Border>
                            <Border Style="{StaticResource CardBorder}">
                              <StackPanel>
                                <TextBlock Text="LOBBY CODE" Foreground="{DynamicResource MutedBrush}" FontSize="10" FontWeight="Bold"/>
                                <TextBox x:Name="LobbyCodeBox" Margin="0,6,0,10"/>
                                <UniformGrid Columns="3">
                                  <Button Content="CREATE LOBBY" Style="{StaticResource AccentButton}" Margin="2" Click="CreateLobby_Click"/>
                                  <Button Content="JOIN LOBBY" Style="{StaticResource RiuButton}" Margin="2" Click="JoinLobby_Click"/>
                                  <Button Content="LEAVE" Style="{StaticResource DangerButton}" Margin="2" Click="LeaveLobby_Click"/>
                                </UniformGrid>
                                <TextBlock x:Name="LobbyStatusText" Text="OFFLINE" Foreground="{DynamicResource AccentBrush}" FontWeight="Bold" Margin="0,12,0,0"/>
                              </StackPanel>
                            </Border>
                          </StackPanel>
                        </ScrollViewer>

'''
if marker in s and 'x:Name="PageLobby"' not in s:
    s=s.replace(marker,lobby+marker,1)
p.write_text(s,encoding="utf-8")

# Route page + physical-only E/V hook.
p,s=read("MainWindow.xaml.cs")
if 'PageLobby.Visibility' not in s:
    s=s.replace('        PageMacros.Visibility = page == "Macros" ? Visibility.Visible : Visibility.Collapsed;',
                '        PageMacros.Visibility = page == "Macros" ? Visibility.Visible : Visibility.Collapsed;\n        PageLobby.Visibility = page == "Lobby" ? Visibility.Visible : Visibility.Collapsed;',1)
if '"Lobby" =>' not in s:
    s=s.replace('            "Macros" => (T("МАКРОСЫ"), T("Два макроса могут выполняться одновременно")),',
                '            "Macros" => (T("МАКРОСЫ"), T("Два макроса могут выполняться одновременно")),\n            "Lobby" => ("LOBBY", "Physical E / V sync"),',1)
p.write_text(s,encoding="utf-8")

p,s=read("MainWindow.Extras.cs")
physical='''        // Only physical hook events reach this method. SendInput from our own
        // macro/clicker is marked and ignored in InputService.
'''
if physical in s and 'BroadcastPhysicalLobbyKey(key);' not in s:
    s=s.replace(physical,physical+'        BroadcastPhysicalLobbyKey(key);\n\n',1)
p.write_text(s,encoding="utf-8")

# Ensure app branding/version says paid 5.22 but preserve 5.22 UI.
for name in ("MainWindow.xaml","MainWindow.xaml.cs","MainWindow.Extras.cs","BrandVisual.cs"):
    p=root/name
    if p.exists():
        t=p.read_text(encoding="utf-8").replace("RiuClicker 1.2","RiuClicker 5.22 PRO").replace("RIUCLICKER 1.2","RIUCLICKER 5.22 PRO")
        p.write_text(t,encoding="utf-8")

p,s=read("RiuClickerCS.csproj")
s=re.sub(r'<Version>[^<]+</Version>','<Version>5.22.0</Version>',s)
s=re.sub(r'<FileVersion>[^<]+</FileVersion>','<FileVersion>5.22.0.0</FileVersion>',s)
s=re.sub(r'<AssemblyVersion>[^<]+</AssemblyVersion>','<AssemblyVersion>5.22.0.0</AssemblyVersion>',s)
p.write_text(s,encoding="utf-8")

print("paid/lobby patch applied")
