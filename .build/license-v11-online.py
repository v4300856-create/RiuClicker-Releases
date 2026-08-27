from pathlib import Path

root = Path('src')

# Final guard for the production 1.1 key system. license-v1.py generates the
# online-only client; this patch additionally enforces a hard 24h client lease.
p = root / 'LicenseService.cs'
s = p.read_text(encoding='utf-8')

# Never allow the old local/test bypass back into a release build.
s = s.replace('    public const string LocalTestKey = "RIU-TEST-1000-0001";\n', '')
s = s.replace('version = "1.0"', 'version = "1.1"')

old_load = '''    public static string? LoadSavedKey()\n    {\n        try\n        {\n            if (!File.Exists(LicenseFile)) return null;\n            using var doc = JsonDocument.Parse(File.ReadAllText(LicenseFile));\n            return doc.RootElement.TryGetProperty("key", out var k) ? k.GetString() : null;\n        }\n        catch { return null; }\n    }\n'''
new_load = '''    public static string? LoadSavedKey()\n    {\n        try\n        {\n            if (!File.Exists(LicenseFile)) return null;\n            using var doc = JsonDocument.Parse(File.ReadAllText(LicenseFile));\n            var root = doc.RootElement;\n            if (!root.TryGetProperty("key", out var k)) return null;\n            if (!root.TryGetProperty("expiresAt", out var exp) || exp.ValueKind != JsonValueKind.String ||\n                !DateTimeOffset.TryParse(exp.GetString(), out var expiresAt) || expiresAt <= DateTimeOffset.UtcNow)\n            {\n                ClearSavedKey();\n                return null;\n            }\n            return k.GetString();\n        }\n        catch { ClearSavedKey(); return null; }\n    }\n'''
if old_load not in s:
    raise SystemExit('LoadSavedKey target missing')
s = s.replace(old_load, new_load)

old_save = '''    public static void SaveKey(string key)\n    {\n        if (string.IsNullOrWhiteSpace(Endpoint)) return;\n        Directory.CreateDirectory(Folder);\n        File.WriteAllText(LicenseFile, JsonSerializer.Serialize(new { key = Normalize(key) }));\n    }\n'''
new_save = '''    public static void SaveKey(string key, DateTimeOffset? serverExpiresAt = null)\n    {\n        if (string.IsNullOrWhiteSpace(Endpoint)) return;\n        Directory.CreateDirectory(Folder);\n        var hardLimit = DateTimeOffset.UtcNow.AddHours(24);\n        var expiresAt = serverExpiresAt is { } server && server < hardLimit ? server : hardLimit;\n        File.WriteAllText(LicenseFile, JsonSerializer.Serialize(new\n        {\n            key = Normalize(key),\n            activatedAt = DateTimeOffset.UtcNow,\n            expiresAt\n        }));\n    }\n'''
if old_save not in s:
    raise SystemExit('SaveKey target missing')
s = s.replace(old_save, new_save)

if 'GetKeyStartUrl()' not in s:
    raise SystemExit('Real GET KEY start URL helper missing')
if 'RIU-TEST-1000-0001' in s:
    raise SystemExit('Local test key is still present')
if 'public const string Endpoint' not in s:
    raise SystemExit('Online license endpoint missing')
if 'hardLimit = DateTimeOffset.UtcNow.AddHours(24)' not in s:
    raise SystemExit('24h client expiry guard missing')

p.write_text(s, encoding='utf-8')

p = root / 'ActivationWindow.xaml'
s = p.read_text(encoding='utf-8')
s = s.replace('Title="RiuClicker 1.0 · License"', 'Title="RiuClicker 1.1 · License"')
s = s.replace('Text="RIUCLICKER 1.0"', 'Text="RIUCLICKER 1.1"')
p.write_text(s, encoding='utf-8')

p = root / 'ActivationWindow.xaml.cs'
s = p.read_text(encoding='utf-8')
if 'LicenseService.SaveKey(key);' in s:
    s = s.replace('LicenseService.SaveKey(key);', 'LicenseService.SaveKey(key, result.ExpiresAt);')
elif 'LicenseService.SaveKey(key, result.ExpiresAt);' not in s:
    raise SystemExit('Activation save target missing')
p.write_text(s, encoding='utf-8')

print('RiuClicker 1.1 production key-system guard applied: online validation + hard 24h local expiry')
