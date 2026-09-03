from pathlib import Path
root=Path('src')
p=root/'Engines.cs'
s=p.read_text(encoding='utf-8')
needle='''        RunningChanged?.Invoke(macro.Id, true);\n        _ = Task.Run(() => RunOwned(macro, settings, cts));'''
if needle in s and 'Макрос «{macro.Name}» запущен' not in s:
    s=s.replace(needle,'''        RunningChanged?.Invoke(macro.Id, true);\n        Message?.Invoke($"Макрос «{macro.Name}» запущен");\n        _ = Task.Run(() => RunOwned(macro, settings, cts));''',1)
p.write_text(s,encoding='utf-8')
print('macro start notification applied')
