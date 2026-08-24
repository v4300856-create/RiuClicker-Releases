from pathlib import Path

p = Path('src/MainWindow.xaml.cs')
s = p.read_text(encoding='utf-8')
lines = s.splitlines()
fixed = False
for i, line in enumerate(lines):
    if 'stats.Text =' in line and 'CPS actual' in line:
        indent = line[:len(line) - len(line.lstrip())]
        lines[i] = indent + 'stats.Text = $"{engine.ClickCount:N0} clicks · {(int)elapsed.TotalMinutes:00}:{elapsed.Seconds:00} · {actualCps:0} CPS actual";'
        fixed = True
        break
if not fixed:
    raise SystemExit('CPS actual stats line missing')
p.write_text('\n'.join(lines) + ('\n' if s.endswith('\n') else ''), encoding='utf-8')
print('Fixed Free v1.0 CPS stats compile line')
