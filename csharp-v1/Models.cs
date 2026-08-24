using System.IO;
using System.Text.Json;

namespace RiuClicker;

public sealed class AppSettings
{
    public ClickerSettings Clicker1 { get; set; } = new() { Hotkey = "F8", Cps = 12, MouseButton = "left" };
    public ClickerSettings Clicker2 { get; set; } = new() { Hotkey = "F7", Cps = 18, MouseButton = "left" };
    public MacroSettings BoltPush { get; set; } = new() { Hotkey = "E", Speed = "fast", Enabled = true, ClickCoordinate = true };
    public MacroSettings Bolts { get; set; } = new() { Hotkey = "V", Speed = "fast", Enabled = true };
    public WallhopSettings Wallhop { get; set; } = new();
    public List<CoordinateItem> Coordinates { get; set; } = [];
    public string BoltPushCoordinateId { get; set; } = "";
    public string Language { get; set; } = "ru";
    public string BackgroundPath { get; set; } = "";
    public bool StartupToast { get; set; } = true;

    public static string PathName => Path.Combine(
        Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData),
        "RiuClicker", "settings-1.0.json");

    public static AppSettings Load()
    {
        try
        {
            if (File.Exists(PathName))
                return JsonSerializer.Deserialize<AppSettings>(File.ReadAllText(PathName)) ?? new();
        }
        catch { }
        return new();
    }

    public void Save()
    {
        Directory.CreateDirectory(Path.GetDirectoryName(PathName)!);
        File.WriteAllText(PathName, JsonSerializer.Serialize(this, new JsonSerializerOptions { WriteIndented = true }));
    }
}

public sealed class ClickerSettings
{
    public string Hotkey { get; set; } = "F8";
    public double Cps { get; set; } = 12;
    public string MouseButton { get; set; } = "left";
}

public sealed class MacroSettings
{
    public bool Enabled { get; set; } = true;
    public string Hotkey { get; set; } = "E";
    public string Speed { get; set; } = "fast";
    public bool ClickCoordinate { get; set; }
}

public sealed class WallhopSettings
{
    public string LeftHotkey { get; set; } = "Z";
    public string RightHotkey { get; set; } = "X";
    public int Pixels { get; set; } = 650;
    public int ReturnDelayMs { get; set; } = 26;
    public bool ReturnCamera { get; set; } = true;
}

public sealed class CoordinateItem
{
    public string Id { get; set; } = Guid.NewGuid().ToString("N");
    public string Name { get; set; } = "Target";
    public int X { get; set; }
    public int Y { get; set; }
}
