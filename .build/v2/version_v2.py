from pathlib import Path
import os,re
root=Path('src')
edition=os.environ.get('RIU_EDITION','FREE').upper()
label='RiuClicker 2.0 PRO' if edition=='PRO' else 'RiuClicker 2.0 FREE'
for p in root.rglob('*'):
    if not p.is_file() or p.suffix.lower() not in ('.cs','.xaml','.csproj'): continue
    try:s=p.read_text(encoding='utf-8')
    except:continue
    s=s.replace('RiuClicker 5.22 PRO',label).replace('RIUCLICKER 5.22 PRO',label.upper())
    s=s.replace('RiuClicker 5.22',label).replace('RIUCLICKER 5.22',label.upper())
    s=s.replace('RiuClicker 1.1',label).replace('RIUCLICKER 1.1',label.upper())
    s=s.replace('RiuClicker 1.2',label).replace('RIUCLICKER 1.2',label.upper())
    s=s.replace('RiuClicker 1.3',label).replace('RIUCLICKER 1.3',label.upper())
    p.write_text(s,encoding='utf-8')
p=root/'RiuClickerCS.csproj'
s=p.read_text(encoding='utf-8')
s=re.sub(r'<Version>[^<]+</Version>','<Version>2.0.0</Version>',s)
s=re.sub(r'<FileVersion>[^<]+</FileVersion>','<FileVersion>2.0.0.0</FileVersion>',s)
s=re.sub(r'<AssemblyVersion>[^<]+</AssemblyVersion>','<AssemblyVersion>2.0.0.0</AssemblyVersion>',s)
p.write_text(s,encoding='utf-8')
print('v2 branding applied:',edition)
