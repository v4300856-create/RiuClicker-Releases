using System.Collections.ObjectModel;
using System.Net.Http;
using System.Text;
using System.Text.Json;
using System.Windows;
using System.Windows.Controls;

namespace RiuClickerAdmin;

public partial class MainWindow : Window
{
    const string Endpoint = "https://rpbjeexhbanaavazfmpo.supabase.co/functions/v1/riu-pro-license";
    readonly HttpClient _http = new() { Timeout = TimeSpan.FromSeconds(15) };
    readonly ObservableCollection<LicenseRow> _items = new();
    string _adminPassword = "";

    public class LicenseRow
    {
        public string Id { get; set; } = "";
        public string Key { get; set; } = "";
        public string Plan { get; set; } = "";
        public string Customer { get; set; } = "—";
        public string Status { get; set; } = "UNUSED";
        public string Device { get; set; } = "—";
        public string Expires { get; set; } = "—";
    }

    public MainWindow()
    {
        InitializeComponent();
        GridKeys.ItemsSource = _items;
        UpdateStats();
    }

    HttpRequestMessage Req(HttpMethod method, string action, object? body = null)
    {
        var req = new HttpRequestMessage(method, Endpoint + "?action=" + action);
        req.Headers.Add("x-admin-password", _adminPassword);
        if (body is not null)
            req.Content = new StringContent(JsonSerializer.Serialize(body), Encoding.UTF8, "application/json");
        return req;
    }

    async Task<JsonDocument?> SendAsync(HttpRequestMessage req)
    {
        try
        {
            using var resp = await _http.SendAsync(req);
            var txt = await resp.Content.ReadAsStringAsync();
            if (string.IsNullOrWhiteSpace(txt)) return null;
            var doc = JsonDocument.Parse(txt);
            if (!resp.IsSuccessStatusCode)
            {
                var err = doc.RootElement.TryGetProperty("error", out var e) ? e.GetString() : resp.StatusCode.ToString();
                MessageBox.Show("Server: " + err, "RiuClicker Admin");
                doc.Dispose();
                return null;
            }
            return doc;
        }
        catch (Exception ex)
        {
            MessageBox.Show("Connection error: " + ex.Message, "RiuClicker Admin");
            return null;
        }
    }

    async void Connect_Click(object sender, RoutedEventArgs e)
    {
        _adminPassword = AdminPasswordBox.Password;
        if (string.IsNullOrWhiteSpace(_adminPassword))
        {
            MessageBox.Show("Enter admin password.", "RiuClicker Admin");
            return;
        }
        await LoadServerKeys();
    }

    async void Refresh_Click(object sender, RoutedEventArgs e) => await LoadServerKeys();

    async Task LoadServerKeys()
    {
        if (string.IsNullOrWhiteSpace(_adminPassword))
        {
            MessageBox.Show("Connect first.", "RiuClicker Admin");
            return;
        }

        using var doc = await SendAsync(Req(HttpMethod.Get, "admin-list"));
        if (doc is null) { ServerStateText.Text = "● AUTH FAILED"; return; }

        _items.Clear();
        foreach (var it in doc.RootElement.GetProperty("items").EnumerateArray())
        {
            string S(string n) => it.TryGetProperty(n, out var v) && v.ValueKind != JsonValueKind.Null ? v.ToString() : "";
            var revoked = it.TryGetProperty("revoked", out var rv) && rv.GetBoolean();
            var hwid = S("hwid_hash");
            var activated = S("activated_at");
            var expires = S("expires_at");
            var plan = S("plan");
            _items.Add(new LicenseRow
            {
                Id = S("id"),
                Key = "RIU-PRO-••••-••••-" + S("key_last4"),
                Plan = plan,
                Customer = string.IsNullOrWhiteSpace(S("customer_note")) ? "—" : S("customer_note"),
                Status = revoked ? "REVOKED" : !string.IsNullOrWhiteSpace(activated) ? "ACTIVE" : "UNUSED",
                Device = string.IsNullOrWhiteSpace(hwid) ? "—" : "BOUND",
                Expires = plan == "LIFETIME" ? "LIFETIME" : string.IsNullOrWhiteSpace(expires) ? "STARTS ON ACTIVATE" : DateTimeOffset.Parse(expires).LocalDateTime.ToString("yyyy-MM-dd HH:mm")
            });
        }

        ServerStateText.Text = "● SERVER ONLINE";
        UpdateStats();
    }

    async void CreateKey_Click(object sender, RoutedEventArgs e)
    {
        if (string.IsNullOrWhiteSpace(_adminPassword))
        {
            MessageBox.Show("Connect first.", "RiuClicker Admin");
            return;
        }

        var plan = (PlanBox.SelectedItem as ComboBoxItem)?.Content?.ToString() ?? "30 DAYS";
        using var doc = await SendAsync(Req(HttpMethod.Post, "admin-create", new
        {
            plan,
            customer = CustomerBox.Text.Trim()
        }));
        if (doc is null) return;

        var key = doc.RootElement.GetProperty("key").GetString() ?? "";
        Clipboard.SetText(key);
        MessageBox.Show("REAL SERVER KEY CREATED + COPIED:\n\n" + key + "\n\nSave/send it now. For security, the full key is shown only at creation.", "RiuClicker Admin");
        CustomerBox.Clear();
        await LoadServerKeys();
    }

    void Copy_Click(object sender, RoutedEventArgs e)
    {
        if ((sender as Button)?.Tag is LicenseRow r)
            Clipboard.SetText(r.Key);
    }

    async void ResetHwid_Click(object sender, RoutedEventArgs e)
    {
        if ((sender as Button)?.Tag is not LicenseRow r) return;
        using var doc = await SendAsync(Req(HttpMethod.Post, "admin-reset-hwid", new { id = r.Id }));
        if (doc is not null) await LoadServerKeys();
    }

    async void Revoke_Click(object sender, RoutedEventArgs e)
    {
        if ((sender as Button)?.Tag is not LicenseRow r) return;
        if (MessageBox.Show("Revoke this key?", "RiuClicker Admin", MessageBoxButton.YesNo) != MessageBoxResult.Yes) return;
        using var doc = await SendAsync(Req(HttpMethod.Post, "admin-revoke", new { id = r.Id }));
        if (doc is not null) await LoadServerKeys();
    }

    void UpdateStats()
    {
        TotalText.Text = _items.Count.ToString();
        ActiveText.Text = _items.Count(x => x.Status == "ACTIVE").ToString();
        LifetimeText.Text = _items.Count(x => x.Plan == "LIFETIME").ToString();
        GridKeys.Items.Refresh();
    }
}