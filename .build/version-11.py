from pathlib import Path
import re

root = Path('src')
for name in ('App.xaml.cs','ActivationWindow.xaml','ActivationWindow.xaml.cs','MainWindow.xaml','MainWindow.xaml.cs','MainWindow.Bolts.cs','Models.cs'):
    p = root / name
    if p.exists():
        s = p.read_text(encoding='utf-8')
        s = s.replace('RiuClicker 1.0', 'RiuClicker 1.1')
        s = s.replace('RIUCLICKER 1.0', 'RIUCLICKER 1.1')
        s = s.replace('version = "1.0"', 'version = "1.1"')
        p.write_text(s, encoding='utf-8')

p = root / 'RiuClickerCS.csproj'
s = p.read_text(encoding='utf-8')
s = re.sub(r'<Version>[^<]+</Version>', '<Version>1.1.0</Version>', s)
s = re.sub(r'<FileVersion>[^<]+</FileVersion>', '<FileVersion>1.1.0.0</FileVersion>', s)
s = re.sub(r'<AssemblyVersion>[^<]+</AssemblyVersion>', '<AssemblyVersion>1.1.0.0</AssemblyVersion>', s)
p.write_text(s, encoding='utf-8')
print('Rebranded current build as RiuClicker 1.1')
