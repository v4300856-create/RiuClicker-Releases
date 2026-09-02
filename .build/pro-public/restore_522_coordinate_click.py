from pathlib import Path
import re

root=Path("src")

# Restore the exact 5.22 coordinate-click behavior inside the current persistent clicker:
# remember current cursor -> teleport to saved coordinate -> click -> restore cursor.
p=root/"Engines.cs"
s=p.read_text(encoding="utf-8")
pattern=r'''private static bool PerformClick\(ClickerSettings settings, Func<string, CoordinateItem\?> resolver\)\n    \{.*?\n    \}'''
replacement=r'''private static bool PerformClick(ClickerSettings settings, Func<string, CoordinateItem?> resolver)
    {
        if (settings.ClickMode == "coordinate")
        {
            if (string.IsNullOrWhiteSpace(settings.SelectedCoordinateId)) return false;
            var coord = resolver(settings.SelectedCoordinateId);
            if (coord?.X is not int x || coord.Y is not int y) return false;

            // 5.22 behavior: save current cursor, teleport for the click,
            // then immediately put the user's cursor back where it was.
            var old = InputService.CursorPosition();
            InputService.SetCursor(x, y);
            try { InputService.MouseClick(settings.MouseButton); }
            finally { InputService.SetCursor(old.X, old.Y); }
            return true;
        }

        InputService.MouseClick(settings.MouseButton);
        return true;
    }'''
ns,n=re.subn(pattern,replacement,s,count=1,flags=re.S)
if n!=1:
    raise SystemExit("PerformClick target not found")
p.write_text(ns,encoding="utf-8")

# Restore/guarantee the 5.22 clicker controls in the UI for both clickers.
p=root/"MainWindow.xaml"
x=p.read_text(encoding="utf-8")
required=[
    'x:Name="C1CursorMode"',
    'x:Name="C1CoordMode"',
    'x:Name="C1Coordinate"',
    'x:Name="C2CursorMode"',
    'x:Name="C2CoordMode"',
    'x:Name="C2Coordinate"',
]
for marker in required:
    if marker not in x:
        raise SystemExit("Missing 5.22 coordinate UI marker: "+marker)

# Use the old 5.22 labels if a later theme renamed them.
x=re.sub(r'(x:Name="C1CursorMode"[^>]*Content=")[^"]*"',r'\1КУРСОР"',x)
x=re.sub(r'(x:Name="C1CoordMode"[^>]*Content=")[^"]*"',r'\1КООРДИНАТА"',x)
x=re.sub(r'(x:Name="C2CursorMode"[^>]*Content=")[^"]*"',r'\1КУРСОР"',x)
x=re.sub(r'(x:Name="C2CoordMode"[^>]*Content=")[^"]*"',r'\1КООРДИНАТА"',x)
p.write_text(x,encoding="utf-8")

# Guarantee the original 5.22 handlers/settings path still exists.
p=root/"MainWindow.xaml.cs"
cs=p.read_text(encoding="utf-8")
for marker in ["ClickMode_Click","CoordinateCombo_Changed","RefreshClickModeStyles"]:
    if marker not in cs:
        raise SystemExit("Missing 5.22 coordinate handler: "+marker)

print("exact 5.22 coordinate click behavior restored")
