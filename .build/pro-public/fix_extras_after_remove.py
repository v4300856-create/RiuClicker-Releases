from pathlib import Path
p=Path("src/MainWindow.Extras.cs")
s=p.read_text(encoding="utf-8")
# Our cleanup can leave one extra ')' after removing the third ClickVClick OR-clause.
s=s.replace('(_settings.Bolts.Bolts.Enabled && string.Equals(_settings.Bolts.Bolts.Hotkey, key, StringComparison.OrdinalIgnoreCase)));',
            '(_settings.Bolts.Bolts.Enabled && string.Equals(_settings.Bolts.Bolts.Hotkey, key, StringComparison.OrdinalIgnoreCase));')
p.write_text(s,encoding="utf-8")
print("fixed Extras syntax after ClickVClick removal")
