from pathlib import Path

root = Path('src')

# Track the actual button currently capturing a hotkey so its label updates immediately.
p = root / 'MainWindow.xaml.cs'
s = p.read_text(encoding='utf-8')
needle = '    private string? _captureTarget;\n'
replacement = '    private string? _captureTarget;\n    private Button? _captureButton;\n    private object? _captureButtonOriginalContent;\n'
if '_captureButtonOriginalContent' not in s:
    if needle not in s:
        raise SystemExit('capture target field not found')
    s = s.replace(needle, replacement, 1)
p.write_text(s, encoding='utf-8')

p = root / 'MainWindow.Extras.cs'
s = p.read_text(encoding='utf-8')

old_capture_block = '''        if (_captureTarget is not null)\n        {\n            if (key == "ESC") { _captureTarget = null; GlobalStatusText.Text = T("Назначение отменено"); return; }\n            AssignCapturedHotkey(_captureTarget, key);\n            _captureTarget = null;\n            return;\n        }\n'''
new_capture_block = '''        if (_captureTarget is not null)\n        {\n            if (key == "ESC")\n            {\n                if (_captureButton is not null && _captureButtonOriginalContent is not null)\n                    _captureButton.Content = _captureButtonOriginalContent;\n                _captureTarget = null;\n                _captureButton = null;\n                _captureButtonOriginalContent = null;\n                GlobalStatusText.Text = T("Назначение отменено");\n                return;\n            }\n\n            var target = _captureTarget;\n            var captureButton = _captureButton;\n            var previousContent = _captureButtonOriginalContent;\n            var assigned = AssignCapturedHotkey(target, key);\n            if (captureButton is not null)\n                captureButton.Content = assigned ? HotkeyCaptureLabel(target, key) : previousContent;\n            _captureTarget = null;\n            _captureButton = null;\n            _captureButtonOriginalContent = null;\n            return;\n        }\n'''
if old_capture_block not in s:
    raise SystemExit('physical capture block not found')
s = s.replace(old_capture_block, new_capture_block, 1)

old_click = '''    private void HotkeyCapture_Click(object sender, RoutedEventArgs e)\n    {\n        if (sender is not Button b || b.Tag is null) return;\n        _captureTarget = b.Tag.ToString();\n        GlobalStatusText.Text = T("Нажми физическую клавишу или Mouse4/Mouse5 · ESC отмена");\n    }\n'''
new_click = '''    private void HotkeyCapture_Click(object sender, RoutedEventArgs e)\n    {\n        if (sender is not Button b || b.Tag is null) return;\n        if (_captureButton is not null && _captureButton != b && _captureButtonOriginalContent is not null)\n            _captureButton.Content = _captureButtonOriginalContent;\n\n        _captureTarget = b.Tag.ToString();\n        _captureButton = b;\n        _captureButtonOriginalContent = b.Content;\n        b.Content = "PRESS KEY…";\n        GlobalStatusText.Text = T("Нажми физическую клавишу или Mouse4/Mouse5 · ESC отмена");\n    }\n\n    private string HotkeyCaptureLabel(string target, string key) => target switch\n    {\n        "pro_boltpush" or "pro_bolts" => $"HOTKEY · {key}",\n        "coordinate" => $"{T("ГОРЯЧАЯ КЛАВИША")} · {key}",\n        _ => $"{T("ЗАПУСК")} · {key}"\n    };\n'''
if old_click not in s:
    raise SystemExit('HotkeyCapture_Click block not found')
s = s.replace(old_click, new_click, 1)

s = s.replace('    private void AssignCapturedHotkey(string target, string key)\n', '    private bool AssignCapturedHotkey(string target, string key)\n', 1)
s = s.replace('''        if (!CanAssignHotkey(target, key, out var conflict))\n        {\n            Log($"Хоткей {key} не назначен: {conflict}");\n            return;\n        }\n''', '''        if (!CanAssignHotkey(target, key, out var conflict))\n        {\n            Log($"Хоткей {key} не назначен: {conflict}");\n            GlobalStatusText.Text = $"{key} · {conflict}";\n            return false;\n        }\n''', 1)
end = '        Log($"Назначено: {key}");\n    }\n\n    private bool CanAssignHotkey'
if end not in s:
    raise SystemExit('AssignCapturedHotkey end not found')
s = s.replace(end, '        Log($"Назначено: {key}");\n        GlobalStatusText.Text = $"HOTKEY · {key}";\n        return true;\n    }\n\n    private bool CanAssignHotkey', 1)

p.write_text(s, encoding='utf-8')

# Version bump.
p = root / 'RiuClickerCS.csproj'
s = p.read_text(encoding='utf-8')
s = s.replace('<Version>1.1.1</Version>', '<Version>1.1.2</Version>')
s = s.replace('<FileVersion>1.1.1.0</FileVersion>', '<FileVersion>1.1.2.0</FileVersion>')
s = s.replace('<AssemblyVersion>1.1.1.0</AssemblyVersion>', '<AssemblyVersion>1.1.2.0</AssemblyVersion>')
p.write_text(s, encoding='utf-8')

print('Applied Pro 1.1.2 instant hotkey label update')
