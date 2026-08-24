using System.Runtime.InteropServices;
namespace RiuClicker;

public static class InputService
{
    [DllImport("user32.dll")] public static extern short GetAsyncKeyState(int vKey);
    [DllImport("user32.dll")] static extern void keybd_event(byte bVk, byte bScan, uint dwFlags, UIntPtr dwExtraInfo);
    [DllImport("user32.dll")] static extern void mouse_event(uint dwFlags, int dx, int dy, int dwData, UIntPtr dwExtraInfo);
    [DllImport("user32.dll")] public static extern bool SetCursorPos(int X, int Y);
    [DllImport("user32.dll")] public static extern bool GetCursorPos(out POINT point);
    public struct POINT { public int X; public int Y; }

    const uint KEYUP = 0x0002;
    const uint M_LEFTDOWN = 0x0002, M_LEFTUP = 0x0004, M_RIGHTDOWN = 0x0008, M_RIGHTUP = 0x0010, M_MIDDLEDOWN = 0x0020, M_MIDDLEUP = 0x0040;
    const uint M_MOVE = 0x0001, M_MOVE_NOCOALESCE = 0x2000;

    public static bool IsDown(int vk) => (GetAsyncKeyState(vk) & 0x8000) != 0;
    public static void KeyDown(string key) { var vk = Vk(key); if (vk != 0) keybd_event((byte)vk, 0, 0, UIntPtr.Zero); }
    public static void KeyUp(string key) { var vk = Vk(key); if (vk != 0) keybd_event((byte)vk, 0, KEYUP, UIntPtr.Zero); }
    public static async Task Tap(string key, int holdMs, CancellationToken ct = default) { KeyDown(key); await Task.Delay(Math.Max(6, holdMs), ct); KeyUp(key); }
    public static void Click(string button)
    {
        var b = button.ToLowerInvariant();
        if (b == "right") { mouse_event(M_RIGHTDOWN,0,0,0,UIntPtr.Zero); mouse_event(M_RIGHTUP,0,0,0,UIntPtr.Zero); }
        else if (b == "middle") { mouse_event(M_MIDDLEDOWN,0,0,0,UIntPtr.Zero); mouse_event(M_MIDDLEUP,0,0,0,UIntPtr.Zero); }
        else { mouse_event(M_LEFTDOWN,0,0,0,UIntPtr.Zero); mouse_event(M_LEFTUP,0,0,0,UIntPtr.Zero); }
    }
    public static void MoveRelative(int dx, int dy) => mouse_event(M_MOVE | M_MOVE_NOCOALESCE, dx, dy, 0, UIntPtr.Zero);
    public static (int X,int Y) Cursor() => GetCursorPos(out var p) ? (p.X,p.Y) : (0,0);

    public static int Vk(string name)
    {
        name = name.Trim().ToUpperInvariant();
        if (name.Length == 1 && char.IsLetterOrDigit(name[0])) return name[0];
        if (name.StartsWith('F') && int.TryParse(name[1..], out var f) && f is >= 1 and <= 24) return 0x70 + f - 1;
        return name switch { "TAB"=>0x09,"ENTER"=>0x0D,"SHIFT"=>0x10,"CTRL"=>0x11,"ALT"=>0x12,"ESC"=>0x1B,"SPACE"=>0x20,"LEFT"=>0x25,"UP"=>0x26,"RIGHT"=>0x27,"DOWN"=>0x28,"INSERT"=>0x2D,"DELETE"=>0x2E,"MOUSE1"=>0x01,"MOUSE2"=>0x02,"MOUSE3"=>0x04,"MOUSE4"=>0x05,"MOUSE5"=>0x06,_=>0 };
    }
    public static IEnumerable<(string Name,int Vk)> CaptureKeys()
    {
        yield return ("MOUSE1",1); yield return ("MOUSE2",2); yield return ("MOUSE3",4); yield return ("MOUSE4",5); yield return ("MOUSE5",6);
        foreach (var k in new[]{"TAB","ENTER","SHIFT","CTRL","ALT","ESC","SPACE","LEFT","UP","RIGHT","DOWN","INSERT","DELETE"}) yield return (k,Vk(k));
        for(char c='0'; c<='9'; c++) yield return (c.ToString(),c);
        for(char c='A'; c<='Z'; c++) yield return (c.ToString(),c);
        for(int i=1;i<=24;i++) yield return ($"F{i}",0x70+i-1);
    }
}
