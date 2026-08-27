from pathlib import Path
import re

root = Path('src')

# Make Click VVV Click coordinates truly one-time configurable in the UI.
p = root / 'MainWindow.xaml'
s = p.read_text(encoding='utf-8')
# Remove RESET COORDS button and clarify the locked behavior.
s = s.replace('Text="SET BOTH COORDS · THEY LOCK AUTOMATICALLY"', 'Text="SET BOTH COORDS ONCE · SAVED PERMANENTLY"')
s = re.sub(r'\s*<Button Content="RESET COORDS"[^>]*/>', '', s)
p.write_text(s, encoding='utf-8')

# Remove the reset handler so there is no in-app path that unlocks the pair.
p = root / 'MainWindow.Bolts.cs'
s = p.read_text(encoding='utf-8')
s = re.sub(
    r'\n\s*private void ClickVClickResetCoords_Click\(object sender, RoutedEventArgs e\)\n\s*\{.*?\n\s*\}\n',
    '\n',
    s,
    flags=re.S,
)
s = s.replace('"SET BOTH COORDS · THEY LOCK AUTOMATICALLY"', '"SET BOTH COORDS ONCE · SAVED PERMANENTLY"')
p.write_text(s, encoding='utf-8')

# Rebrand build metadata to 1.2.
p = root / 'RiuClickerCS.csproj'
s = p.read_text(encoding='utf-8')
s = re.sub(r'<Version>[^<]+</Version>', '<Version>1.2.0</Version>', s)
s = re.sub(r'<FileVersion>[^<]+</FileVersion>', '<FileVersion>1.2.0.0</FileVersion>', s)
s = re.sub(r'<AssemblyVersion>[^<]+</AssemblyVersion>', '<AssemblyVersion>1.2.0.0</AssemblyVersion>', s)
p.write_text(s, encoding='utf-8')

for name in ('MainWindow.xaml','MainWindow.xaml.cs','MainWindow.Extras.cs','BrandVisual.cs','Models.cs','ActivationWindow.xaml'):
    p = root / name
    if p.exists():
        text = p.read_text(encoding='utf-8').replace('RiuClicker 1.1','RiuClicker 1.2').replace('RIUCLICKER 1.1','RIUCLICKER 1.2')
        p.write_text(text, encoding='utf-8')

print('Applied RiuClicker 1.2 permanent one-time coordinate lock')
