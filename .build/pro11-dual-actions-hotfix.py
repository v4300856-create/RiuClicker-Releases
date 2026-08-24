from pathlib import Path

root = Path('src')

# Allow both ready-made Pro actions to be enabled at the same time.
p = root / 'Models.cs'
s = p.read_text(encoding='utf-8')
s = s.replace('        if (s.ProActions.BoltPush.Enabled && s.ProActions.Bolts.Enabled) s.ProActions.Bolts.Enabled = false;\n', '')
p.write_text(s, encoding='utf-8')

p = root / 'MainWindow.Pro.cs'
s = p.read_text(encoding='utf-8')
old = '''    private void ProActionToggle_Changed(object sender, RoutedEventArgs e)
    {
        if (_initializing) return;
        if (sender == BoltPushEnabled && BoltPushEnabled.IsChecked == true)
        {
            _settings.ProActions.BoltPush.Enabled = true;
            _settings.ProActions.Bolts.Enabled = false;
        }
        else if (sender == BoltsEnabled && BoltsEnabled.IsChecked == true)
        {
            _settings.ProActions.Bolts.Enabled = true;
            _settings.ProActions.BoltPush.Enabled = false;
        }
        else
        {
            _settings.ProActions.BoltPush.Enabled = BoltPushEnabled.IsChecked == true;
            _settings.ProActions.Bolts.Enabled = BoltsEnabled.IsChecked == true;
        }
        Save();
        RefreshProUi();
    }
'''
new = '''    private void ProActionToggle_Changed(object sender, RoutedEventArgs e)
    {
        if (_initializing) return;
        _settings.ProActions.BoltPush.Enabled = BoltPushEnabled.IsChecked == true;
        _settings.ProActions.Bolts.Enabled = BoltsEnabled.IsChecked == true;
        Save();
        RefreshProUi();
    }
'''
if old not in s:
    raise SystemExit('Pro toggle mutex block not found')
s = s.replace(old, new, 1)
p.write_text(s, encoding='utf-8')

p = root / 'MainWindow.xaml'
s = p.read_text(encoding='utf-8')
s = s.replace('Ready-made combat macros. Bolt Push and Bolts cannot be armed at the same time.',
              'Ready-made combat macros. Bolt Push and Bolts can be armed together with separate hotkeys and speeds.')
p.write_text(s, encoding='utf-8')

print('Applied Pro dual-action enable hotfix')
