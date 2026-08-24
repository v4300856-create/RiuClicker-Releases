using System.ComponentModel;
using System.Windows;
using System.Windows.Media;

namespace RiuClicker;

public partial class MainWindow : Window
{
    private readonly LobbyService _lobby = new();

    public MainWindow()
    {
        InitializeComponent();
        _lobby.MembersChanged += members => Dispatcher.Invoke(() => UpdateMembers(members));
        _lobby.StatusChanged += status => Dispatcher.Invoke(() => StatusText.Text = status);
        _lobby.RoleChanged += role => Dispatcher.Invoke(() => UpdateRole(role));
        _lobby.Log += text => Dispatcher.Invoke(() => AddLog(text));
        _lobby.PingChanged += ping => Dispatcher.Invoke(() => PingText.Text = ping < 0 ? "PING —" : $"PING {ping} ms");
        _lobby.ActionReceived += (from, action) => Dispatcher.Invoke(() => AddLog($"{from} → {action}"));
        AddLog("Lobby ready");
    }

    private async void Host_Click(object sender, RoutedEventArgs e)
    {
        try
        {
            SetBusy(true);
            if (!int.TryParse(PortBox.Text.Trim(), out int port)) port = 42871;
            string code = await _lobby.HostAsync(NameBox.Text, port);
            CodeBox.Text = code;
            JoinCodeBox.Text = code;
            AddLog("Share the code with your friend");
        }
        catch (Exception ex)
        {
            AddLog("Host error: " + ex.Message);
            MessageBox.Show(ex.Message, "RiuClicker Lobby", MessageBoxButton.OK, MessageBoxImage.Error);
        }
        finally { SetBusy(false); }
    }

    private async void Join_Click(object sender, RoutedEventArgs e)
    {
        try
        {
            SetBusy(true);
            await _lobby.JoinAsync(JoinCodeBox.Text, NameBox.Text);
        }
        catch (Exception ex)
        {
            AddLog("Join error: " + ex.Message);
            MessageBox.Show(ex.Message, "RiuClicker Lobby", MessageBoxButton.OK, MessageBoxImage.Error);
        }
        finally { SetBusy(false); }
    }

    private async void Leave_Click(object sender, RoutedEventArgs e)
    {
        await _lobby.StopAsync();
        CodeBox.Text = "";
        AddLog("Left lobby");
    }

    private void CopyCode_Click(object sender, RoutedEventArgs e)
    {
        if (string.IsNullOrWhiteSpace(CodeBox.Text)) return;
        Clipboard.SetText(CodeBox.Text);
        AddLog("Lobby code copied");
    }

    private async void TestSignal_Click(object sender, RoutedEventArgs e)
    {
        try
        {
            await _lobby.SendActionAsync("SYNC_TEST");
            AddLog("Test signal sent");
        }
        catch (Exception ex)
        {
            AddLog("Signal error: " + ex.Message);
        }
    }

    private void UpdateMembers(IReadOnlyList<string> members)
    {
        MembersList.ItemsSource = members.Select(name => $"●  {name}").ToList();
        MemberCountText.Text = $"{members.Count} ONLINE";
    }

    private void UpdateRole(string role)
    {
        RoleText.Text = role;
        StatusDot.Fill = role switch
        {
            "OWNER" => new SolidColorBrush(Color.FromRgb(34, 211, 238)),
            "MEMBER" => new SolidColorBrush(Color.FromRgb(139, 92, 246)),
            _ => new SolidColorBrush(Color.FromRgb(100, 116, 139))
        };
        if (role == "OWNER") PingText.Text = "DIRECT";
        else if (role == "OFFLINE") PingText.Text = "PING —";
    }

    private void AddLog(string text)
    {
        string line = $"[{DateTime.Now:HH:mm:ss.fff}]  {text}";
        LogList.Items.Add(line);
        while (LogList.Items.Count > 120) LogList.Items.RemoveAt(0);
        LogList.ScrollIntoView(LogList.Items[^1]);
    }

    private void SetBusy(bool busy)
    {
        HostButton.IsEnabled = !busy;
        JoinButton.IsEnabled = !busy;
        StatusText.Text = busy ? "Connecting…" : StatusText.Text;
    }

    protected override void OnClosing(CancelEventArgs e)
    {
        base.OnClosing(e);
        _ = _lobby.DisposeAsync();
    }
}
