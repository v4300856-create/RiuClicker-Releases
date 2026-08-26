from pathlib import Path

root = Path('src')

# Force the 1.1 client to use the real online backend only.
p = root / 'LicenseService.cs'
s = p.read_text(encoding='utf-8')
s = s.replace('    public const string LocalTestKey = "RIU-TEST-1000-0001";\n', '')
old = '''        // Temporary local gate until the real production endpoint is configured.\n        // This key is session-only and cannot bypass the next launch.\n        if (string.IsNullOrWhiteSpace(Endpoint))\n        {\n            if (string.Equals(key, LocalTestKey, StringComparison.Ordinal))\n                return new() { Ok = true, Message = "Local test license accepted.", Plan = "TEST" };\n            return new() { Ok = false, Message = "Invalid key. License server is not configured yet." };\n        }\n'''
new = '''        if (string.IsNullOrWhiteSpace(Endpoint))\n            return new() { Ok = false, Message = "License service is not configured." };\n'''
if old not in s:
    raise SystemExit('Temporary local license block not found')
s = s.replace(old, new)
s = s.replace('version = "1.0"', 'version = "1.1"')
p.write_text(s, encoding='utf-8')

# Make the key window clearly belong to 1.1 and explain the flow.
p = root / 'ActivationWindow.xaml'
s = p.read_text(encoding='utf-8')
s = s.replace('Title="RiuClicker 1.0 · License"', 'Title="RiuClicker 1.1 · License"')
s = s.replace('Text="RIUCLICKER 1.0"', 'Text="RIUCLICKER 1.1"')
s = s.replace('Text="Enter your key. Without a valid key RiuClicker will not open."', 'Text="Press GET KEY, complete Loot-Link, copy the generated key, then activate it here."')
p.write_text(s, encoding='utf-8')

print('RiuClicker 1.1 online-only license patch applied')
