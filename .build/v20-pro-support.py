from pathlib import Path

root=Path("src")
p=root/"InputService.cs"
s=p.read_text(encoding="utf-8")

if 'public static void KeyDown(string name)' not in s:
    target='''    public static void TapKey(string name, int holdMs, CancellationToken token)
    {
        if (!TryVirtualKey(name, out var vk)) return;
        Key(vk, false);
        if (holdMs > 0 && token.WaitHandle.WaitOne(holdMs)) { Key(vk, true); return; }
        Key(vk, true);
    }
'''
    addition=target+'''\n    public static void KeyDown(string name)
    {
        if (TryVirtualKey(name, out var vk)) Key(vk, false);
    }

    public static void KeyUp(string name)
    {
        if (TryVirtualKey(name, out var vk)) Key(vk, true);
    }
'''
    if target not in s: raise SystemExit("TapKey marker missing")
    s=s.replace(target,addition,1)

if 'public static void MouseDown(string button)' not in s:
    marker='    public static void MouseClick(string button)\n'
    idx=s.find(marker)
    if idx<0: raise SystemExit("MouseClick marker missing")
    helper=r'''    public static void MouseDown(string button)
    {
        button = button.ToLowerInvariant();
        var (down, _, data) = button switch
        {
            "right" or "mouse2" => (0x0008u, 0x0010u, 0u),
            "middle" or "mouse3" => (0x0020u, 0x0040u, 0u),
            "x1" or "mouse4" => (0x0080u, 0x0100u, 1u),
            "x2" or "mouse5" => (0x0080u, 0x0100u, 2u),
            _ => (0x0002u, 0x0004u, 0u)
        };
        SendMouse(down, 0, 0, data);
    }

    public static void MouseUp(string button)
    {
        button = button.ToLowerInvariant();
        var (_, up, data) = button switch
        {
            "right" or "mouse2" => (0x0008u, 0x0010u, 0u),
            "middle" or "mouse3" => (0x0020u, 0x0040u, 0u),
            "x1" or "mouse4" => (0x0080u, 0x0100u, 1u),
            "x2" or "mouse5" => (0x0080u, 0x0100u, 2u),
            _ => (0x0002u, 0x0004u, 0u)
        };
        SendMouse(up, 0, 0, data);
    }

'''
    s=s[:idx]+helper+s[idx:]
p.write_text(s,encoding="utf-8")

print("PRO v2 trace input support applied")
