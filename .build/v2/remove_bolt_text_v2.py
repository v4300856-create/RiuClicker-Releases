from pathlib import Path
root=Path('src')
for p in root.rglob('*'):
    if not p.is_file() or p.suffix.lower() not in ('.cs','.xaml'): continue
    try:s=p.read_text(encoding='utf-8')
    except:continue
    s=s.replace('V из Bolt Push внутри программы не отправляется участникам.','Синхронизируются только физические E / V владельца.')
    s=s.replace('Bolt Push','удалённый макрос')
    s=s.replace('BOLT PUSH','УДАЛЁННЫЙ МАКРОС')
    p.write_text(s,encoding='utf-8')
print('remaining Bolt text removed')
