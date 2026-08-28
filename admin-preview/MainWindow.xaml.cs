using System.Collections.ObjectModel;
using System.IO;
using System.Security.Cryptography;
using System.Text.Json;
using System.Windows;
using System.Windows.Controls;

namespace RiuClickerAdmin;

public partial class MainWindow : Window
{
    public class LicenseRow
    {
        public string Key { get; set; } = "";
        public string Plan { get; set; } = "";
        public string Customer { get; set; } = "";
        public string Status { get; set; } = "UNUSED";
        public string Device { get; set; } = "—";
    }

    readonly ObservableCollection<LicenseRow> _items = new();
    readonly string _file = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData), "RiuClickerAdmin", "licenses.json");

    public MainWindow()
    {
        InitializeComponent();
        GridKeys.ItemsSource = _items;
        LoadData();
        UpdateStats();
    }

    static string MakeBlock()
    {
        const string chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789";
        Span<byte> b = stackalloc byte[4];
        RandomNumberGenerator.Fill(b);
        return new string(b.ToArray().Select(x => chars[x % chars.Length]).ToArray());
    }

    static string NewKey() => $"RIU-PRO-{MakeBlock()}-{MakeBlock()}-{MakeBlock()}";

    void CreateKey_Click(object sender, RoutedEventArgs e)
    {
        var plan = (PlanBox.SelectedItem as ComboBoxItem)?.Content?.ToString() ?? "30 DAYS";
        var row = new LicenseRow { Key = NewKey(), Plan = plan, Customer = string.IsNullOrWhiteSpace(CustomerBox.Text) ? "—" : CustomerBox.Text.Trim() };
        _items.Insert(0, row);
        SaveData();
        UpdateStats();
        Clipboard.SetText(row.Key);
        MessageBox.Show("Ключ создан и скопирован:\n" + row.Key, "RiuClicker Admin");
    }

    void Copy_Click(object sender, RoutedEventArgs e)
    {
        if ((sender as Button)?.Tag is LicenseRow r) Clipboard.SetText(r.Key);
    }

    void ResetHwid_Click(object sender, RoutedEventArgs e)
    {
        if ((sender as Button)?.Tag is LicenseRow r)
        {
            r.Device = "—";
            r.Status = r.Status == "REVOKED" ? "REVOKED" : "UNUSED";
            GridKeys.Items.Refresh(); SaveData(); UpdateStats();
        }
    }

    void Revoke_Click(object sender, RoutedEventArgs e)
    {
        if ((sender as Button)?.Tag is LicenseRow r)
        {
            r.Status = "REVOKED";
            GridKeys.Items.Refresh(); SaveData(); UpdateStats();
        }
    }

    void UpdateStats()
    {
        TotalText.Text = _items.Count.ToString();
        ActiveText.Text = _items.Count(x => x.Status == "ACTIVE").ToString();
        LifetimeText.Text = _items.Count(x => x.Plan == "LIFETIME").ToString();
    }

    void SaveData()
    {
        Directory.CreateDirectory(Path.GetDirectoryName(_file)!);
        File.WriteAllText(_file, JsonSerializer.Serialize(_items, new JsonSerializerOptions { WriteIndented = true }));
    }

    void LoadData()
    {
        try
        {
            if (!File.Exists(_file)) return;
            var rows = JsonSerializer.Deserialize<List<LicenseRow>>(File.ReadAllText(_file)) ?? new();
            foreach (var r in rows) _items.Add(r);
        }
        catch { }
    }
}