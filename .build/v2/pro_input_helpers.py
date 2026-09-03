from pathlib import Path

p=Path('src/InputService.cs')
s=p.read_text(encoding='utf-8')

if 'public static void KeyDown(string name)' not in s:
    marker='''    public static void TapKey(string name, int holdMs, CancellationToken token)\n    {\n        if (!TryVirtualKey(name, out var vk)) return;\n        Key(vk, false);\n        if (holdMs > 0 && token.WaitHandle.WaitOne(holdMs)) { Key(vk, true); return; }\n        Key(vk, true);\n    }\n'''
    if marker not in s: raise SystemExit('TapKey marker missing')
    s=s.replace(marker,marker+'''\n    public static void KeyDown(string name)\n    {\n        if (TryVirtualKey(name, out var vk)) Key(vk, false);\n    }\n\n    public static void KeyUp(string name)\n    {\n        if (TryVirtualKey(name, out var vk)) Key(vk, true);\n    }\n''',1)

if 'public static void MouseDown(string button)' not in s:
    marker='    public static void MouseClick(string button)\n'
    i=s.find(marker)
    if i<0: raise SystemExit('MouseClick marker missing')
    helper=r'''    public static void MouseDown(string button)
    {
        button=button.ToLowerInvariant();
        var (down,_,data)=button switch
        {
            "right" or "mouse2" => (0x0008u,0x0010u,0u),
            "middle" or "mouse3" => (0x0020u,0x0040u,0u),
            "x1" or "mouse4" => (0x0080u,0x0100u,1u),
            "x2" or "mouse5" => (0x0080u,0x0100u,2u),
            _ => (0x0002u,0x0004u,0u)
        };
        SendMouse(down,0,0,data);
    }

    public static void MouseUp(string button)
    {
        button=button.ToLowerInvariant();
        var (_,up,data)=button switch
        {
            "right" or "mouse2" => (0x0008u,0x0010u,0u),
            "middle" or "mouse3" => (0x0020u,0x0040u,0u),
            "x1" or "mouse4" => (0x0080u,0x0100u,1u),
            "x2" or "mouse5" => (0x0080u,0x0100u,2u),
            _ => (0x0002u,0x0004u,0u)
        };
        SendMouse(up,0,0,data);
    }

'''
    s=s[:i]+helper+s[i:]

p.write_text(s,encoding='utf-8')
print('PRO input helpers applied without Bolts')
