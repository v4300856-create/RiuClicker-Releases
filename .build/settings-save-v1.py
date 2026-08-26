from pathlib import Path

root = Path('src')
main = root / 'MainWindow.xaml.cs'
s = main.read_text(encoding='utf-8')

if 'InstallPersistenceAutosave();' not in s:
    marker = 'InitializeComponent();'
    if marker not in s:
        raise SystemExit('InitializeComponent marker missing')
    s = s.replace(marker, marker + '\n        InstallPersistenceAutosave();', 1)
    main.write_text(s, encoding='utf-8')

(root / 'MainWindow.Persistence.cs').write_text(r'''using System.ComponentModel;
using System.Windows.Input;
using System.Windows.Threading;

namespace RiuClickerCS;

public partial class MainWindow
{
    private DispatcherTimer? _settingsSaveTimer;

    private void InstallPersistenceAutosave()
    {
        _settingsSaveTimer = new DispatcherTimer
        {
            Interval = TimeSpan.FromMilliseconds(220)
        };
        _settingsSaveTimer.Tick += (_, _) =>
        {
            _settingsSaveTimer?.Stop();
            PersistSettingsSafely();
        };

        // Save after normal mouse/keyboard edits. The short debounce lets the
        // existing UI handlers update _settings first, then persists the final state.
        PreviewMouseUp += (_, _) => QueueSettingsSave();
        PreviewKeyUp += (_, _) => QueueSettingsSave();
        Deactivated += (_, _) => PersistSettingsSafely();
        Closing += PersistSettingsOnClosing;
    }

    private void QueueSettingsSave()
    {
        if (_initializing || _settingsSaveTimer is null) return;
        _settingsSaveTimer.Stop();
        _settingsSaveTimer.Start();
    }

    private void PersistSettingsOnClosing(object? sender, CancelEventArgs e)
    {
        _settingsSaveTimer?.Stop();
        PersistSettingsSafely();
    }

    private void PersistSettingsSafely()
    {
        if (_initializing) return;
        try { Save(); }
        catch { }
    }
}
''', encoding='utf-8')

print('Applied persistent settings autosave')
