from pathlib import Path

root = Path('src')

# Final guard for the production 1.1 key system. license-v1.py now generates the
# online-only client directly, so this patch only verifies/enforces key details.
p = root / 'LicenseService.cs'
s = p.read_text(encoding='utf-8')

# Never allow the old local/test bypass back into a release build.
s = s.replace('    public const string LocalTestKey = "RIU-TEST-1000-0001";\n', '')
s = s.replace('version = "1.0"', 'version = "1.1"')

if 'GetKeyStartUrl()' not in s:
    raise SystemExit('Real GET KEY start URL helper missing')
if 'RIU-TEST-1000-0001' in s:
    raise SystemExit('Local test key is still present')
if 'public const string Endpoint' not in s:
    raise SystemExit('Online license endpoint missing')

p.write_text(s, encoding='utf-8')

p = root / 'ActivationWindow.xaml'
s = p.read_text(encoding='utf-8')
s = s.replace('Title="RiuClicker 1.0 · License"', 'Title="RiuClicker 1.1 · License"')
s = s.replace('Text="RIUCLICKER 1.0"', 'Text="RIUCLICKER 1.1"')
p.write_text(s, encoding='utf-8')

print('RiuClicker 1.1 production online key-system guard applied')
