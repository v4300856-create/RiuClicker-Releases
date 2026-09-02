from pathlib import Path

root=Path("src")

p=root/"InputService.cs"
s=p.read_text(encoding="utf-8")
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

p=root/"MainWindow.Bolts.cs"
s=p.read_text(encoding="utf-8")
old='''                InputService.SetCursor(x, y);
                await BoltDelay(t.PointerSettle);
                InputService.MouseClickHeld("left", t.ClickHold, CancellationToken.None);
                await BoltDelay(t.AfterClick);
'''
new='''                // Teleport once to the saved coordinate, press there,
                // then never touch cursor position again so the user can move immediately.
                InputService.SetCursor(x, y);
                InputService.MouseDown("left");
                await BoltDelay(Math.Max(10, t.ClickHold));
                InputService.MouseUp("left");
                await BoltDelay(t.AfterClick);
'''
if old not in s:
    raise SystemExit("Bolt Push final click target missing")
s=s.replace(old,new,1)
p.write_text(s,encoding="utf-8")
print("PRO Bolt Push one-teleport cursor fix applied")
