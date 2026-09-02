from pathlib import Path
import re

src=Path("src/App.xaml")
base=Path("private-build/base-App.xaml")

if not base.exists():
    raise SystemExit("base App.xaml backup missing")

s=base.read_text(encoding="utf-8")

# Remove only automatic StartupUri. Keep every original 5.22 resource/style/dictionary.
s=re.sub(r'\s+StartupUri\s*=\s*"[^"]*"', '', s, count=1, flags=re.I)

# Ensure our app class remains the paid App code-behind.
s=re.sub(r'x:Class\s*=\s*"[^"]+"', 'x:Class="RiuClickerCS.App"', s, count=1)

src.write_text(s,encoding="utf-8")

if "Application.Resources" not in s:
    raise SystemExit("restored App.xaml has no Application.Resources")

print("restored original 5.22 App.xaml resources")
