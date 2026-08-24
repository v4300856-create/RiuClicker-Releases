from pathlib import Path

root = Path('src')

def rw(name):
    p = root / name
    return p, p.read_text(encoding='utf-8')

def save(p, s):
    p.write_text(s, encoding='utf-8')

# Keep product version at 1.0 while retaining the reliability/UI fixes.
p, s = rw('RiuClickerCS.csproj')
s = s.replace('<Version>1.1.0</Version>', '<Version>1.0.0</Version>')
s = s.replace('<AssemblyVersion>1.1.0.0</AssemblyVersion>', '<AssemblyVersion>1.0.0.0</AssemblyVersion>')
s = s.replace('<FileVersion>1.1.0.0</FileVersion>', '<FileVersion>1.0.0.0</FileVersion>')
save(p, s)

p, s = rw('Models.cs')
s = s.replace('public const string DefaultIntro = "Free RiuClicker 1.1";', 'public const string DefaultIntro = "Free RiuClicker · Fixed";')
save(p, s)

p, s = rw('BrandVisual.cs')
s = s.replace('Title = "Free RiuClicker 1.1 · Pulse";', 'Title = "Free RiuClicker 1.0 · Fixed";')
s = s.replace('HeaderBrandVersionText.Text = "PULSE UI  •  FREE 1.1";', 'HeaderBrandVersionText.Text = "PULSE UI  •  FIXED";')
s = s.replace('SidebarBrandVersionText.Text = "1.1  •  PULSE";', 'SidebarBrandVersionText.Text = "1.0  •  FIXED";')
save(p, s)

p, s = rw('MainWindow.xaml')
s = s.replace('Title="Free RiuClicker 1.1 · Pulse"', 'Title="Free RiuClicker 1.0 · Fixed"')
s = s.replace('Text="1.1  •  PULSE"', 'Text="1.0  •  FIXED"')
s = s.replace('Text="FREE 1.1 · PULSE UI"', 'Text="FREE 1.0 · FIXED"')
save(p, s)

print('Free RiuClicker 1.0 Fixed labels applied')
