from pathlib import Path
import re

root=Path("src")

# ---------- InputService: physical mouse movement + Roblox foreground check ----------
p=root/"InputService.cs"
s=p.read_text(encoding="utf-8")
s=s.replace(
'    private const int WM_LBUTTONDOWN = 0x0201, WM_LBUTTONUP = 0x0202, WM_RBUTTONDOWN = 0x0204, WM_RBUTTONUP = 0x0205;',
'    private const int WM_MOUSEMOVE = 0x0200, WM_LBUTTONDOWN = 0x0201, WM_LBUTTONUP = 0x0202, WM_RBUTTONDOWN = 0x0204, WM_RBUTTONUP = 0x0205;'
)
if 'public event Action<int,int>? PhysicalMouseMove;' not in s:
    s=s.replace('    public event Action<string>? PhysicalUp;','    public event Action<string>? PhysicalUp;\n    public event Action<int,int>? PhysicalMouseMove;')

needle='''                var msg = wParam.ToInt32();
                string? name = msg switch
'''
if needle in s and 'PhysicalMouseMove?.Invoke' not in s:
    s=s.replace(needle,'''                var msg = wParam.ToInt32();
                if (msg == WM_MOUSEMOVE) PhysicalMouseMove?.Invoke(data.pt.X, data.pt.Y);
                string? name = msg switch
''',1)

if 'public static bool IsRobloxForeground()' not in s:
    marker='    public static bool TryVirtualKey(string raw, out ushort vk)'
    helper=r'''    public static bool IsRobloxForeground()
    {
        try
        {
            var hwnd = GetForegroundWindow();
            if (hwnd == IntPtr.Zero) return false;
            GetWindowThreadProcessId(hwnd, out var pid);
            if (pid == 0) return false;
            using var p = Process.GetProcessById((int)pid);
            var n = p.ProcessName ?? "";
            return n.Contains("Roblox", StringComparison.OrdinalIgnoreCase);
        }
        catch { return false; }
    }

'''
    if marker not in s: raise SystemExit("TryVirtualKey marker missing")
    s=s.replace(marker,helper+marker,1)
    s=s.replace('[DllImport("user32.dll")] private static extern bool SetCursorPos(int X, int Y);',
                '[DllImport("user32.dll")] private static extern bool SetCursorPos(int X, int Y);\n    [DllImport("user32.dll")] private static extern IntPtr GetForegroundWindow();\n    [DllImport("user32.dll")] private static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint processId);')
p.write_text(s,encoding="utf-8")

# ---------- LobbyService with consent-gated Trace calls ----------
(root/"LobbyService.cs").write_text(r'''using System.Net.Http;
using System.Text;
using System.Text.Json;

namespace RiuClickerCS;

public sealed class LobbyEventItem
{
    public long Id { get; set; }
    public string Action { get; set; } = "";
}

public sealed class LobbyService
{
    const string Endpoint="https://rpbjeexhbanaavazfmpo.supabase.co/functions/v1/riu-pro-lobby";
    readonly HttpClient _http=new(){Timeout=TimeSpan.FromSeconds(10)};

    async Task<JsonDocument?> Call(object payload)
    {
        try
        {
            using var req=new HttpRequestMessage(HttpMethod.Post,Endpoint)
            {
                Content=new StringContent(JsonSerializer.Serialize(payload),Encoding.UTF8,"application/json")
            };
            using var res=await _http.SendAsync(req);
            var txt=await res.Content.ReadAsStringAsync();
            if(!res.IsSuccessStatusCode)return null;
            return JsonDocument.Parse(txt);
        }
        catch{return null;}
    }

    object Base(string action,string code="")=>new
    {
        action,code,key=PaidLicenseService.LoadKey(),hwid=PaidLicenseService.DeviceId()
    };

    public async Task<(bool ok,string code,string ownerToken)> Create()
    {
        using var d=await Call(Base("create")); if(d is null)return(false,"","");
        var r=d.RootElement;
        return(r.GetProperty("ok").GetBoolean(),r.GetProperty("code").GetString()??"",r.GetProperty("owner_token").GetString()??"");
    }

    public async Task<(bool ok,long lastId)> Join(string code)
    {
        using var d=await Call(Base("join",code)); if(d is null)return(false,0);
        var r=d.RootElement; return(r.GetProperty("ok").GetBoolean(),r.TryGetProperty("last_id",out var i)?i.GetInt64():0);
    }

    public async Task<bool> Push(string code,string ownerToken,string ev)
    {
        using var d=await Call(new{action="push",code,owner_token=ownerToken,@event=ev,key=PaidLicenseService.LoadKey(),hwid=PaidLicenseService.DeviceId()});
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

    public async Task<(bool ok,string token)> RequestTrace(string code)
    {
        using var d=await Call(Base("trace_request",code)); if(d is null)return(false,"");
        var r=d.RootElement;
        return(r.TryGetProperty("ok",out var ok)&&ok.GetBoolean(),
               r.TryGetProperty("controller_token",out var t)?t.GetString()??"":"");
    }

    public async Task<(bool ok,bool pending,bool approved)> TracePending(string code,string ownerToken)
    {
        using var d=await Call(new{action="trace_pending",code,owner_token=ownerToken,key=PaidLicenseService.LoadKey(),hwid=PaidLicenseService.DeviceId()});
        if(d is null)return(false,false,false);
        var r=d.RootElement;
        return(r.TryGetProperty("ok",out var ok)&&ok.GetBoolean(),
               r.TryGetProperty("pending",out var p)&&p.GetBoolean(),
               r.TryGetProperty("approved",out var a)&&a.GetBoolean());
    }

    public async Task<bool> SetTraceApproval(string code,string ownerToken,bool allow)
    {
        using var d=await Call(new{action=allow?"trace_allow":"trace_deny",code,owner_token=ownerToken,key=PaidLicenseService.LoadKey(),hwid=PaidLicenseService.DeviceId()});
        return d is not null && d.RootElement.TryGetProperty("ok",out var ok)&&ok.GetBoolean();
    }

    public async Task<(bool ok,bool approved)> TraceStatus(string code,string controllerToken)
    {
        using var d=await Call(new{action="trace_status",code,controller_token=controllerToken,key=PaidLicenseService.LoadKey(),hwid=PaidLicenseService.DeviceId()});
        if(d is null)return(false,false);
        var r=d.RootElement;
        return(r.TryGetProperty("ok",out var ok)&&ok.GetBoolean(),
               r.TryGetProperty("approved",out var a)&&a.GetBoolean());
    }

    public async Task<bool> TracePush(string code,string controllerToken,string ev)
    {
        using var d=await Call(new{action="trace_push",code,controller_token=controllerToken,@event=ev,key=PaidLicenseService.LoadKey(),hwid=PaidLicenseService.DeviceId()});
        return d is not null && d.RootElement.TryGetProperty("ok",out var ok)&&ok.GetBoolean();
    }
}
''',encoding="utf-8")

# ---------- Lobby controller ----------
(root/"MainWindow.Lobby.cs").write_text(r'''using System.Diagnostics;
using System.Windows;

namespace RiuClickerCS;

public partial class MainWindow
{
    readonly LobbyService _lobby=new();
    CancellationTokenSource? _lobbyPollCts;
    string _lobbyCode="",_lobbyOwnerToken="",_traceControllerToken="";
    long _lobbyLastId;
    bool _lobbyOwner,_traceApproved,_traceOwnerAllowed,_tracePromptOpen;
    int _lobbyPollTick;
    long _traceMouseLastTicks;
    int _traceMouseX,_traceMouseY;
    bool _traceMouseHavePoint;

    private async void CreateLobby_Click(object sender,RoutedEventArgs e)
    {
        LeaveLobby(); LobbyStatusText.Text="CREATING...";
        var r=await _lobby.Create();
        if(!r.ok){LobbyStatusText.Text="CREATE FAILED";return;}
        _lobbyCode=r.code;_lobbyOwnerToken=r.ownerToken;_lobbyOwner=true;_lobbyLastId=0;
        LobbyCodeBox.Text=r.code;LobbyStatusText.Text="OWNER · ONLINE";
        TraceStatusText.Text="TRACE · WAITING FOR REQUEST";
        StartLobbyPoll();
    }

    private async void JoinLobby_Click(object sender,RoutedEventArgs e)
    {
        LeaveLobby();
        var code=LobbyCodeBox.Text.Trim().ToUpperInvariant();
        LobbyStatusText.Text="JOINING...";
        var r=await _lobby.Join(code);
        if(!r.ok){LobbyStatusText.Text="LOBBY NOT FOUND";return;}
        _lobbyCode=code;_lobbyOwner=false;_lobbyLastId=r.lastId;
        LobbyStatusText.Text="MEMBER · ONLINE";
        TraceStatusText.Text="TRACE · NOT REQUESTED";
        StartLobbyPoll();
    }

    private async void RequestTrace_Click(object sender,RoutedEventArgs e)
    {
        if(_lobbyOwner || string.IsNullOrWhiteSpace(_lobbyCode))
        {
            TraceStatusText.Text="TRACE · JOIN A LOBBY AS MEMBER";
            return;
        }
        TraceStatusText.Text="TRACE · REQUESTING...";
        var r=await _lobby.RequestTrace(_lobbyCode);
        if(!r.ok){TraceStatusText.Text="TRACE · REQUEST FAILED";return;}
        _traceControllerToken=r.token;
        _traceApproved=false;
        TraceStatusText.Text="TRACE · WAITING FOR OWNER ALLOW";
    }

    private async void AllowTrace_Click(object sender,RoutedEventArgs e)
    {
        if(!_lobbyOwner || string.IsNullOrWhiteSpace(_lobbyCode))return;
        var ok=await _lobby.SetTraceApproval(_lobbyCode,_lobbyOwnerToken,true);
        _traceOwnerAllowed=ok;
        TraceStatusText.Text=ok?"TRACE · ALLOWED · ROBLOX ONLY":"TRACE · ALLOW FAILED";
    }

    private async void DenyTrace_Click(object sender,RoutedEventArgs e)
    {
        if(!_lobbyOwner || string.IsNullOrWhiteSpace(_lobbyCode))return;
        await _lobby.SetTraceApproval(_lobbyCode,_lobbyOwnerToken,false);
        _traceOwnerAllowed=false;
        ReleaseTraceKeys();
        TraceStatusText.Text="TRACE · BLOCKED";
    }

    private void LeaveLobby_Click(object sender,RoutedEventArgs e)=>LeaveLobby();

    private void LeaveLobby()
    {
        _lobbyPollCts?.Cancel();_lobbyPollCts=null;
        _lobbyCode="";_lobbyOwnerToken="";_traceControllerToken="";
        _lobbyOwner=false;_lobbyLastId=0;_traceApproved=false;_traceOwnerAllowed=false;_tracePromptOpen=false;
        _traceMouseHavePoint=false;
        ReleaseTraceKeys();
        if(LobbyStatusText is not null)LobbyStatusText.Text="OFFLINE";
        if(TraceStatusText is not null)TraceStatusText.Text="TRACE · OFF";
    }

    private void StartLobbyPoll(){_lobbyPollCts=new();_=LobbyPollLoop(_lobbyPollCts.Token);}

    private async Task LobbyPollLoop(CancellationToken token)
    {
        while(!token.IsCancellationRequested&&!string.IsNullOrWhiteSpace(_lobbyCode))
        {
            _lobbyPollTick++;
            var events=await _lobby.Poll(_lobbyCode,_lobbyLastId);
            foreach(var ev in events)
            {
                _lobbyLastId=Math.Max(_lobbyLastId,ev.Id);
                if(!_lobbyOwner&&(ev.Action=="E"||ev.Action=="V"))
                    InputService.TapKey(ev.Action,10,CancellationToken.None);
                else if(_lobbyOwner && ev.Action.StartsWith("TR:",StringComparison.OrdinalIgnoreCase))
                    ApplyTraceEvent(ev.Action[3..]);
            }

            if(_lobbyPollTick%4==0)
            {
                if(_lobbyOwner)
                {
                    var p=await _lobby.TracePending(_lobbyCode,_lobbyOwnerToken);
                    _traceOwnerAllowed=p.ok&&p.approved;
                    if(p.ok&&p.pending&&!_tracePromptOpen)
                    {
                        _tracePromptOpen=true;
                        await Dispatcher.InvokeAsync(async ()=>{
                            var answer=MessageBox.Show(
                                "Участник просит TRACE управление игровым вводом.\n\nРазрешить WASD / Space / Shift / E / V / мышь только когда Roblox активен?\n\nF12 мгновенно отключает управление.",
                                "RiuClicker PRO · TRACE REQUEST",
                                MessageBoxButton.YesNo,
                                MessageBoxImage.Warning);
                            if(answer==MessageBoxResult.Yes)
                            {
                                _traceOwnerAllowed=await _lobby.SetTraceApproval(_lobbyCode,_lobbyOwnerToken,true);
                                TraceStatusText.Text=_traceOwnerAllowed?"TRACE · ALLOWED · ROBLOX ONLY":"TRACE · ALLOW FAILED";
                            }
                            else
                            {
                                await _lobby.SetTraceApproval(_lobbyCode,_lobbyOwnerToken,false);
                                _traceOwnerAllowed=false;
                                TraceStatusText.Text="TRACE · BLOCKED";
                            }
                            _tracePromptOpen=false;
                        });
                    }
                }
                else if(!string.IsNullOrWhiteSpace(_traceControllerToken))
                {
                    var s=await _lobby.TraceStatus(_lobbyCode,_traceControllerToken);
                    _traceApproved=s.ok&&s.approved;
                    TraceStatusText.Text=_traceApproved?"TRACE · ACTIVE · ROBLOX ONLY":"TRACE · WAITING FOR OWNER ALLOW";
                }
            }

            try{await Task.Delay(80,token);}catch{break;}
        }
    }

    private void BroadcastPhysicalLobbyKey(string key)
    {
        if(!_lobbyOwner||string.IsNullOrWhiteSpace(_lobbyCode))return;
        if(key!="E"&&key!="V")return;
        _=_lobby.Push(_lobbyCode,_lobbyOwnerToken,key);
    }

    private static bool TraceKeyAllowed(string key)
        => key is "W" or "A" or "S" or "D" or "SPACE" or "SHIFT" or "E" or "V";

    private void TracePhysicalKey(string key,bool down)
    {
        if(_lobbyOwner||!_traceApproved||string.IsNullOrWhiteSpace(_traceControllerToken))return;
        if(!InputService.IsRobloxForeground())return;
        key=key.ToUpperInvariant();
        string? ev=null;
        if(TraceKeyAllowed(key))ev=(down?"KD:":"KU:")+key;
        else if(key is "MOUSE1" or "MOUSE2")ev=(down?"MD:":"MU:")+key;
        if(ev is not null)_=_lobby.TracePush(_lobbyCode,_traceControllerToken,ev);
    }

    private void TracePhysicalMouseMove(int x,int y)
    {
        if(_lobbyOwner||!_traceApproved||string.IsNullOrWhiteSpace(_traceControllerToken))return;
        if(!InputService.IsRobloxForeground()){_traceMouseHavePoint=false;return;}
        if(!_traceMouseHavePoint){_traceMouseX=x;_traceMouseY=y;_traceMouseHavePoint=true;return;}

        var now=Stopwatch.GetTimestamp();
        var elapsedMs=(now-_traceMouseLastTicks)*1000.0/Stopwatch.Frequency;
        if(elapsedMs<32)return;

        var dx=Math.Clamp(x-_traceMouseX,-120,120);
        var dy=Math.Clamp(y-_traceMouseY,-120,120);
        _traceMouseX=x;_traceMouseY=y;_traceMouseLastTicks=now;
        if(dx==0&&dy==0)return;
        _=_lobby.TracePush(_lobbyCode,_traceControllerToken,$"MM:{dx},{dy}");
    }

    private void ApplyTraceEvent(string ev)
    {
        if(!_traceOwnerAllowed)return;
        if(!InputService.IsRobloxForeground())return;
        try
        {
            if(ev.StartsWith("KD:")){var k=ev[3..];if(TraceKeyAllowed(k))InputService.KeyDown(k);}
            else if(ev.StartsWith("KU:")){var k=ev[3..];if(TraceKeyAllowed(k))InputService.KeyUp(k);}
            else if(ev=="MD:MOUSE1")InputService.MouseDown("left");
            else if(ev=="MU:MOUSE1")InputService.MouseUp("left");
            else if(ev=="MD:MOUSE2")InputService.MouseDown("right");
            else if(ev=="MU:MOUSE2")InputService.MouseUp("right");
            else if(ev.StartsWith("MM:"))
            {
                var a=ev[3..].Split(',');
                if(a.Length==2&&int.TryParse(a[0],out var dx)&&int.TryParse(a[1],out var dy))
                    InputService.MoveMouseRelative(Math.Clamp(dx,-120,120),Math.Clamp(dy,-120,120));
            }
        }
        catch{}
    }

    private void ReleaseTraceKeys()
    {
        foreach(var k in new[]{"W","A","S","D","SPACE","SHIFT","E","V"})InputService.KeyUp(k);
        InputService.MouseUp("left");InputService.MouseUp("right");
    }

    private void DisableTraceEmergency()
    {
        _traceApproved=false;
        _traceOwnerAllowed=false;
        ReleaseTraceKeys();
        if(_lobbyOwner&&!string.IsNullOrWhiteSpace(_lobbyCode))
            _=_lobby.SetTraceApproval(_lobbyCode,_lobbyOwnerToken,false);
        if(TraceStatusText is not null)TraceStatusText.Text="TRACE · STOPPED BY F12";
    }
}
''',encoding="utf-8")

# ---------- MainWindow subscription + physical key relay ----------
p=root/"MainWindow.xaml.cs"
s=p.read_text(encoding="utf-8")
if '_input.PhysicalMouseMove +=' not in s:
    s=s.replace('_input.PhysicalUp += key => Dispatcher.BeginInvoke(() => OnPhysicalUp(key));',
                '_input.PhysicalUp += key => Dispatcher.BeginInvoke(() => OnPhysicalUp(key));\n        _input.PhysicalMouseMove += (x,y) => TracePhysicalMouseMove(x,y);')
p.write_text(s,encoding="utf-8")

p=root/"MainWindow.Extras.cs"
s=p.read_text(encoding="utf-8")
if 'DisableTraceEmergency();' not in s:
    s=s.replace('    private void StopAll()\n    {','    private void StopAll()\n    {\n        DisableTraceEmergency();',1)
if 'TracePhysicalKey(key,true);' not in s:
    s=s.replace('''        if (key == "F12")
        {
            StopAll();
            return;
        }
''','''        if (key == "F12")
        {
            StopAll();
            return;
        }

        TracePhysicalKey(key,true);
''',1)
if 'TracePhysicalKey(key,false);' not in s:
    s=s.replace('''        key = key.ToUpperInvariant();
        _physicalDown.Remove(key);
''','''        key = key.ToUpperInvariant();
        _physicalDown.Remove(key);
        TracePhysicalKey(key,false);
''',1)
p.write_text(s,encoding="utf-8")

# ---------- Lobby UI: explicit consent controls + visible status ----------
p=root/"MainWindow.xaml"
s=p.read_text(encoding="utf-8")
if 'x:Name="TraceStatusText"' not in s:
    target='''                                <Button Content="ВЫЙТИ" Style="{StaticResource DangerButton}" Click="LeaveLobby_Click"/>
'''
    addition=target+'''                                <Border Margin="0,14,0,0" Padding="14" CornerRadius="14" BorderBrush="{DynamicResource BorderBrush}" BorderThickness="1">
                                  <StackPanel>
                                    <TextBlock Text="TRACE LOBBY · ROBLOX ONLY" Foreground="{DynamicResource AccentBrush}" FontSize="13" FontWeight="Bold"/>
                                    <TextBlock Text="Только после ALLOW хозяина. Управление: WASD, Space, Shift, E/V, движение мыши и ЛКМ/ПКМ. Работает только когда Roblox активен. F12 отключает TRACE." Foreground="{DynamicResource MutedBrush}" Margin="0,6,0,10" TextWrapping="Wrap"/>
                                    <Button Content="REQUEST TRACE CONTROL" Style="{StaticResource RiuButton}" Margin="0,0,0,7" Click="RequestTrace_Click"/>
                                    <Grid>
                                      <Grid.ColumnDefinitions><ColumnDefinition/><ColumnDefinition/></Grid.ColumnDefinitions>
                                      <Button Content="ALLOW TRACE" Style="{StaticResource AccentButton}" Margin="0,0,4,0" Click="AllowTrace_Click"/>
                                      <Button Grid.Column="1" Content="DENY / STOP TRACE" Style="{StaticResource DangerButton}" Margin="4,0,0,0" Click="DenyTrace_Click"/>
                                    </Grid>
                                    <TextBlock x:Name="TraceStatusText" Text="TRACE · OFF" Foreground="{DynamicResource AccentBrush}" FontWeight="Bold" Margin="0,10,0,0"/>
                                  </StackPanel>
                                </Border>
'''
    if target not in s: raise SystemExit("Lobby leave button marker missing")
    s=s.replace(target,addition,1)
p.write_text(s,encoding="utf-8")

# Validation.
alltext="\n".join(fp.read_text(encoding="utf-8",errors="ignore") for fp in root.glob("*") if fp.suffix in (".cs",".xaml"))
for marker in ["TRACE LOBBY","REQUEST TRACE CONTROL","TracePhysicalMouseMove","IsRobloxForeground","DisableTraceEmergency","trace_request","trace_push"]:
    if marker not in alltext: raise SystemExit("missing trace marker: "+marker)
print("consent-gated Roblox-only Trace Lobby applied")
