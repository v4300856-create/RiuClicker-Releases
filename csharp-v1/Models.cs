using System.Text.Json;
namespace RiuClicker;

public sealed class AppSettings
{
    public ClickerSettings Clicker1 { get; set; } = new() { Hotkey = "F8" };
    public ClickerSettings Clicker2 { get; set; } = new() { Hotkey = "F7" };
    public MacroSettings BoltPush { get; set; } = new() { Hotkey = "E", Speed = "fast" };
    public MacroSettings Bolts { get; set; } = new() { Hotkey = "V", Speed = "fast" };
    public WallhopSettings Wallhop { get; set; } = new();
    public List<CoordinateItem> Coordinates { get; set; } = [];
    public string BoltPushCoordinateId { get; set; } = "";
    public string Language { get; set; } = "ru";
    public string BackgroundPath { get; set; } = "";

    public static string PathName => System.IO.Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData), "RiuClicker", "settings-1.0.json");
    public static AppSettings Load()
    {
        try { if (File.Exists(PathName)) return JsonSerializer.Deserialize<AppSettings>(File.ReadAllText(PathName)) ?? new(); } catch { }
        return new();
    }
    public void Save()
    {
        Directory.CreateDirectory(System.IO.Path.GetDirectoryName(PathName)!);
        File.WriteAllText(PathName, JsonSerializer.Serialize(this, new JsonSerializerOptions { WriteIndented = true }));
    }
}
public sealed class ClickerSettings { public string Hotkey { get; set; } = "F8"; public double Cps { get; set; } = 12; public string MouseButton { get; set; } = "left"; }
public sealed class MacroSettings { public bool Enabled { get; set; } = true; public string Hotkey { get; set; } = "E"; public string Speed { get; set; } = "fast"; }
public sealed class WallhopSettings { public string Hotkey { get; set; } = "Q"; public string Direction { get; set; } = "right"; public int Pixels { get; set; } = 650; public int ReturnDelayMs { get; set; } = 26; public bool ReturnCamera { get; set; } = true; }
public sealed class CoordinateItem { public string Id { get; set; } = Guid.NewGuid().ToString("N"); public string Name { get; set; } = "Target"; public int X { get; set; } public int Y { get; set; } }
