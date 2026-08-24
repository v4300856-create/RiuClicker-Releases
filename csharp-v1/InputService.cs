using System.Runtime.InteropServices;

namespace RiuClicker;

public static class InputService
{
    private const uint INPUT_MOUSE = 0;
    private const uint INPUT_KEYBOARD = 1;
    private const uint KEYEVENTF_KEYUP = 0x0002;
    private const uint MOUSEEVENTF_MOVE = 0x0001;
    private const uint MOUSEEVENTF_LEFTDOWN = 0x0002;
    private const uint MOUSEEVENTF_LEFTUP = 0x0004;
    private const uint MOUSEEVENTF_RIGHTDOWN = 0x0008;
    private const uint MOUSEEVENTF_RIGHTUP = 0x0010;
    private const uint MOUSEEVENTF_MIDDLEDOWN = 0x0020;
    private const uint MOUSEEVENTF_MIDDLEUP = 0x0040;

    [StructLayout(LayoutKind.Sequential)]
    private struct INPUT
    {
        public uint type;
        public INPUTUNION U;
    }

    [StructLayout(LayoutKind.Explicit)]
    private struct INPUTUNION
    {
        [FieldOffset(0)] public MOUSEINPUT mi;
        [FieldOffset(0)] public KEYBDINPUT ki;
    }

    [StructLayout(LayoutKind.Sequential)]
    private struct MOUSEINPUT
    {
        public int dx;
        public int dy;
        public uint mouseData;
        public uint dwFlags;
        public uint time;
        public UIntPtr dwExtraInfo;
    }

    [StructLayout(LayoutKind.Sequential)]
    private struct KEYBDINPUT
    {
        public ushort wVk;
        public ushort wScan;
        public uint dwFlags;
        public uint time;
        public UIntPtr dwExtraInfo;
    }

    [StructLayout(LayoutKind.Sequential)]
    public struct POINT
    {
        public int X;
        public int Y;
    }

    [DllImport("user32.dll", SetLastError = true)]
    private static extern uint SendInput(uint nInputs, INPUT[] pInputs, int cbSize);

    [DllImport("user32.dll")]
    public static extern short GetAsyncKeyState(int vKey);

    [DllImport("user32.dll")]
    public static extern bool SetCursorPos(int X, int Y);

    [DllImport("user32.dll")]
    public static extern bool GetCursorPos(out POINT point);

    public static bool IsDown(int vk) => (GetAsyncKeyState(vk) & 0x8000) != 0;

    public static void KeyDown(string key) => SendKey(key, false);
    public static void KeyUp(string key) => SendKey(key, true);

    private static void SendKey(string key, bool up)
    {
        int vk = Vk(key);
        if (vk == 0) return;
        var input = new INPUT
        {
            type = INPUT_KEYBOARD,
            U = new INPUTUNION
            {
                ki = new KEYBDINPUT
                {
                    wVk = (ushort)vk,
                    dwFlags = up ? KEYEVENTF_KEYUP : 0
                }
            }
        };
        SendInput(1, [input], Marshal.SizeOf<INPUT>());
    }

    public static async Task Tap(string key, int holdMs, CancellationToken ct = default)
    {
        KeyDown(key);
        try { await Task.Delay(Math.Clamp(holdMs, 8, 80), ct); }
        finally { KeyUp(key); }
    }

    public static void Click(string button)
    {
        uint down;
        uint up;
        switch ((button ?? "left").Trim().ToLowerInvariant())
        {
            case "right": down = MOUSEEVENTF_RIGHTDOWN; up = MOUSEEVENTF_RIGHTUP; break;
            case "middle": down = MOUSEEVENTF_MIDDLEDOWN; up = MOUSEEVENTF_MIDDLEUP; break;
            default: down = MOUSEEVENTF_LEFTDOWN; up = MOUSEEVENTF_LEFTUP; break;
        }
        var inputs = new[]
        {
            new INPUT { type = INPUT_MOUSE, U = new INPUTUNION { mi = new MOUSEINPUT { dwFlags = down } } },
            new INPUT { type = INPUT_MOUSE, U = new INPUTUNION { mi = new MOUSEINPUT { dwFlags = up } } }
        };
        SendInput((uint)inputs.Length, inputs, Marshal.SizeOf<INPUT>());
    }

    public static void MoveRelative(int dx, int dy)
    {
        var input = new INPUT
        {
            type = INPUT_MOUSE,
            U = new INPUTUNION
            {
                mi = new MOUSEINPUT { dx = dx, dy = dy, dwFlags = MOUSEEVENTF_MOVE }
            }
        };
        SendInput(1, [input], Marshal.SizeOf<INPUT>());
    }

    public static (int X, int Y) Cursor() => GetCursorPos(out var p) ? (p.X, p.Y) : (0, 0);

    public static async Task ClickAtAsync(int x, int y, string button = "left", bool restoreCursor = true, CancellationToken ct = default)
    {
        var old = Cursor();
        SetCursorPos(x, y);
        await Task.Delay(8, ct);
        Click(button);
        if (restoreCursor)
        {
            await Task.Delay(8, ct);
            SetCursorPos(old.X, old.Y);
        }
    }

    public static int Vk(string name)
    {
        name = (name ?? "").Trim().ToUpperInvariant();
        if (name.Length == 1 && char.IsLetterOrDigit(name[0])) return name[0];
        if (name.StartsWith('F') && int.TryParse(name[1..], out var f) && f is >= 1 and <= 24) return 0x70 + f - 1;
        return name switch
        {
            "TAB" => 0x09, "ENTER" => 0x0D, "SHIFT" => 0x10, "CTRL" => 0x11, "ALT" => 0x12,
            "ESC" => 0x1B, "SPACE" => 0x20, "LEFT" => 0x25, "UP" => 0x26, "RIGHT" => 0x27,
            "DOWN" => 0x28, "INSERT" => 0x2D, "DELETE" => 0x2E,
            "MOUSE1" => 0x01, "MOUSE2" => 0x02, "MOUSE3" => 0x04, "MOUSE4" => 0x05, "MOUSE5" => 0x06,
            _ => 0
        };
    }

    public static IEnumerable<(string Name, int Vk)> CaptureKeys()
    {
        yield return ("MOUSE1", 1); yield return ("MOUSE2", 2); yield return ("MOUSE3", 4); yield return ("MOUSE4", 5); yield return ("MOUSE5", 6);
        foreach (var k in new[] { "TAB", "ENTER", "SHIFT", "CTRL", "ALT", "ESC", "SPACE", "LEFT", "UP", "RIGHT", "DOWN", "INSERT", "DELETE" })
            yield return (k, Vk(k));
        for (char c = '0'; c <= '9'; c++) yield return (c.ToString(), c);
        for (char c = 'A'; c <= 'Z'; c++) yield return (c.ToString(), c);
        for (int i = 1; i <= 24; i++) yield return ($"F{i}", 0x70 + i - 1);
    }
}
