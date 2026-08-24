using Microsoft.Win32;
using System.ComponentModel;
using System.IO;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Media.Animation;
using System.Windows.Media.Imaging;

namespace RiuClicker;

public partial class MainWindow : Window
{
    private AppSettings _settings = new();
    private EngineService? _engine;
    private bool _loading = true;

    public MainWindow()
    {
        InitializeComponent();
        _settings = AppSettings.Load();
        _engine = new EngineService(_settings);
        _engine.FeatureStateChanged += (feature, state) => Dispatcher.Invoke(() => UpdateFeatureState(feature, state));
        _engine.StatusChanged += text => Dispatcher.Invoke(() => StatusText.Text = text);
        _engine.EmergencyStopped += () => Dispatcher.Invoke(UpdateHomeSummary);
        BackgroundVideo.MediaEnded += (_, _) => { BackgroundVideo.Position = TimeSpan.Zero; BackgroundVideo.Play(); };
        Loaded += MainWindow_Loaded;
        ApplySettingsToUi();
        _loading = false;
    }

    private void MainWindow_Loaded(object sender, RoutedEventArgs e)
    {
        Navigate("Home");
        ApplyBackground();
        ApplyLanguage();
        UpdateHomeSummary();
        if (_settings.StartupToast) ShowStartupToast();
    }

    private void ApplySettingsToUi()
    {
        Clicker1HotkeyButton.Content = _settings.Clicker1.Hotkey;
        Clicker2HotkeyButton.Content = _settings.Clicker2.Hotkey;
        Clicker1CpsSlider.Value = Math.Clamp(_settings.Clicker1.Cps, 1, 60);
        Clicker2CpsSlider.Value = Math.Clamp(_settings.Clicker2.Cps, 1, 60);
        SelectByTag(Clicker1MouseCombo, _settings.Clicker1.MouseButton);
        SelectByTag(Clicker2MouseCombo, _settings.Clicker2.MouseButton);

        BoltPushHotkeyButton.Content = _settings.BoltPush.Hotkey;
        BoltsHotkeyButton.Content = _settings.Bolts.Hotkey;
        BoltPushEnabledCheck.IsChecked = _settings.BoltPush.Enabled;
        BoltsEnabledCheck.IsChecked = _settings.Bolts.Enabled;
        BoltPushCoordCheck.IsChecked = _settings.BoltPush.ClickCoordinate;
        SelectByTag(BoltPushSpeedCombo, _settings.BoltPush.Speed);
        SelectByTag(BoltsSpeedCombo, _settings.Bolts.Speed);

        WallhopLeftHotkeyButton.Content = _settings.Wallhop.LeftHotkey;
        WallhopRightHotkeyButton.Content = _settings.Wallhop.RightHotkey;
        WallhopPixelsSlider.Value = Math.Clamp(_settings.Wallhop.Pixels, 50, 1600);
        WallhopDelaySlider.Value = Math.Clamp(_settings.Wallhop.ReturnDelayMs, 1, 120);
        WallhopReturnCheck.IsChecked = _settings.Wallhop.ReturnCamera;

        SelectByTag(LanguageCombo, _settings.Language);
        StartupToastCheck.IsChecked = _settings.StartupToast;
        RefreshCoordinates();
        UpdateLabels();
        BackgroundPathText.Text = string.IsNullOrWhiteSpace(_settings.BackgroundPath) ? "Default" : _settings.BackgroundPath;
    }

    private static void SelectByTag(ComboBox combo, string value)
    {
        foreach (var item in combo.Items.OfType<ComboBoxItem>())
        {
            if (string.Equals(item.Tag?.ToString(), value, StringComparison.OrdinalIgnoreCase))
            {
                combo.SelectedItem = item;
                return;
            }
        }
        if (combo.Items.Count > 0) combo.SelectedIndex = 0;
    }

    private static string SelectedTag(ComboBox combo, string fallback)
        => (combo.SelectedItem as ComboBoxItem)?.Tag?.ToString() ?? fallback;

    private void Nav_Click(object sender, RoutedEventArgs e)
    {
        if (sender is Button button) Navigate(button.Tag?.ToString() ?? "Home");
    }

    private void Navigate(string page)
    {
        HomePage.Visibility = page == "Home" ? Visibility.Visible : Visibility.Collapsed;
        ClickersPage.Visibility = page == "Clickers" ? Visibility.Visible : Visibility.Collapsed;
        MacrosPage.Visibility = page == "Macros" ? Visibility.Visible : Visibility.Collapsed;
        CoordsPage.Visibility = page == "Coords" ? Visibility.Visible : Visibility.Collapsed;
        WallhopPage.Visibility = page == "Wallhop" ? Visibility.Visible : Visibility.Collapsed;
        SettingsPage.Visibility = page == "Settings" ? Visibility.Visible : Visibility.Collapsed;

        foreach (var button in new[] { HomeNav, ClickersNav, MacrosNav, CoordsNav, WallhopNav, SettingsNav })
        {
            bool active = string.Equals(button.Tag?.ToString(), page, StringComparison.OrdinalIgnoreCase);
            button.Background = active ? new SolidColorBrush(Color.FromRgb(27, 35, 51)) : Brushes.Transparent;
            button.Foreground = active ? Brushes.White : new SolidColorBrush(Color.FromRgb(141, 152, 173));
        }
    }

    private void OpenMacros_Click(object sender, RoutedEventArgs e) => Navigate("Macros");

    private async void HotkeyButton_Click(object sender, RoutedEventArgs e)
    {
        if (_engine is null || sender is not Button button) return;
        string old = button.Content?.ToString() ?? "—";
        button.IsEnabled = false;
        button.Content = "PRESS KEY…";
        StatusText.Text = "Нажми нужную клавишу…";
        try
        {
            string key = await _engine.CaptureHotkeyAsync();
            switch (button.Tag?.ToString())
            {
                case "clicker1": _settings.Clicker1.Hotkey = key; break;
                case "clicker2": _settings.Clicker2.Hotkey = key; break;
                case "boltpush": _settings.BoltPush.Hotkey = key; break;
                case "bolts": _settings.Bolts.Hotkey = key; break;
                case "wallleft": _settings.Wallhop.LeftHotkey = key; break;
                case "wallright": _settings.Wallhop.RightHotkey = key; break;
            }
            button.Content = key;
            SaveQuiet();
            UpdateHomeSummary();
            StatusText.Text = $"Hotkey: {key}";
        }
        catch (Exception ex)
        {
            button.Content = old;
            StatusText.Text = "Hotkey: " + ex.Message;
        }
        finally { button.IsEnabled = true; }
    }

    private void ClickerCps_ValueChanged(object sender, RoutedPropertyChangedEventArgs<double> e)
    {
        if (_loading) return;
        _settings.Clicker1.Cps = Math.Round(Clicker1CpsSlider.Value);
        _settings.Clicker2.Cps = Math.Round(Clicker2CpsSlider.Value);
        UpdateLabels();
        UpdateHomeSummary();
    }

    private void MouseCombo_SelectionChanged(object sender, SelectionChangedEventArgs e)
    {
        if (_loading) return;
        _settings.Clicker1.MouseButton = SelectedTag(Clicker1MouseCombo, "left");
        _settings.Clicker2.MouseButton = SelectedTag(Clicker2MouseCombo, "left");
        SaveQuiet();
    }

    private void ToggleClicker_Click(object sender, RoutedEventArgs e)
    {
        if (_engine is null || sender is not Button button) return;
        if (button.Tag?.ToString() == "1") _engine.ToggleClicker(1); else _engine.ToggleClicker(2);
    }

    private void UpdateFeatureState(string feature, bool active)
    {
        if (feature == "clicker1")
        {
            HomeClicker1State.Text = active ? "ON" : "OFF";
            HomeClicker1State.Foreground = new SolidColorBrush(active ? Color.FromRgb(94, 230, 177) : Color.FromRgb(255, 118, 139));
        }
        else if (feature == "clicker2")
        {
            HomeClicker2State.Text = active ? "ON" : "OFF";
            HomeClicker2State.Foreground = new SolidColorBrush(active ? Color.FromRgb(94, 230, 177) : Color.FromRgb(255, 118, 139));
        }
    }

    private void MacroSetting_Changed(object sender, RoutedEventArgs e)
    {
        if (_loading) return;
        _settings.BoltPush.Enabled = BoltPushEnabledCheck.IsChecked == true;
        _settings.Bolts.Enabled = BoltsEnabledCheck.IsChecked == true;
        _settings.BoltPush.ClickCoordinate = BoltPushCoordCheck.IsChecked == true;
        _settings.BoltPush.Speed = SelectedTag(BoltPushSpeedCombo, "fast");
        _settings.Bolts.Speed = SelectedTag(BoltsSpeedCombo, "fast");
        SaveQuiet();
        UpdateHomeSummary();
    }

    private async void ArmF6_Click(object sender, RoutedEventArgs e)
    {
        if (_engine is null) return;
        ArmF6Button.IsEnabled = false;
        ArmF6Button.Content = "WAITING F6…";
        StatusText.Text = "Наведи мышь на точку и нажми F6";
        try
        {
            await _engine.WaitForKeyAsync("F6");
            var pos = InputService.Cursor();
            var point = new CoordinateItem
            {
                Name = $"Point {_settings.Coordinates.Count + 1}",
                X = pos.X,
                Y = pos.Y
            };
            _settings.Coordinates.Add(point);
            _settings.BoltPushCoordinateId = point.Id;
            SaveQuiet();
            RefreshCoordinates();
            CoordinatesList.SelectedIndex = _settings.Coordinates.Count - 1;
            StatusText.Text = $"Saved X:{point.X} Y:{point.Y}";
        }
        catch (Exception ex) { StatusText.Text = "F6: " + ex.Message; }
        finally
        {
            ArmF6Button.Content = "ARM F6";
            ArmF6Button.IsEnabled = true;
        }
    }

    private void CoordinatesList_SelectionChanged(object sender, SelectionChangedEventArgs e)
    {
        if (_loading || CoordinatesList.SelectedIndex < 0 || CoordinatesList.SelectedIndex >= _settings.Coordinates.Count) return;
        _settings.BoltPushCoordinateId = _settings.Coordinates[CoordinatesList.SelectedIndex].Id;
        SaveQuiet();
        RefreshActiveCoordinate();
    }

    private void DeleteCoord_Click(object sender, RoutedEventArgs e)
    {
        int index = CoordinatesList.SelectedIndex;
        if (index < 0 || index >= _settings.Coordinates.Count) return;
        string id = _settings.Coordinates[index].Id;
        _settings.Coordinates.RemoveAt(index);
        if (_settings.BoltPushCoordinateId == id)
            _settings.BoltPushCoordinateId = _settings.Coordinates.FirstOrDefault()?.Id ?? "";
        SaveQuiet();
        RefreshCoordinates();
    }

    private void RefreshCoordinates()
    {
        CoordinatesList.ItemsSource = _settings.Coordinates.Select(c => $"{c.Name}    X:{c.X}  Y:{c.Y}").ToList();
        int active = _settings.Coordinates.FindIndex(c => c.Id == _settings.BoltPushCoordinateId);
        if (active >= 0) CoordinatesList.SelectedIndex = active;
        RefreshActiveCoordinate();
    }

    private void RefreshActiveCoordinate()
    {
        var point = _settings.Coordinates.FirstOrDefault(c => c.Id == _settings.BoltPushCoordinateId);
        ActiveCoordText.Text = point is null ? (_settings.Language == "en" ? "Not selected" : "Не выбрано") : $"X:{point.X} · Y:{point.Y}";
    }

    private void WallhopSetting_Changed(object sender, RoutedEventArgs e)
    {
        if (_loading) return;
        _settings.Wallhop.Pixels = (int)Math.Round(WallhopPixelsSlider.Value);
        _settings.Wallhop.ReturnDelayMs = (int)Math.Round(WallhopDelaySlider.Value);
        _settings.Wallhop.ReturnCamera = WallhopReturnCheck.IsChecked == true;
        UpdateLabels();
        SaveQuiet();
    }

    private void LanguageCombo_SelectionChanged(object sender, SelectionChangedEventArgs e)
    {
        if (_loading) return;
        _settings.Language = SelectedTag(LanguageCombo, "ru");
        ApplyLanguage();
        SaveQuiet();
    }

    private void ApplyLanguage()
    {
        bool en = string.Equals(_settings.Language, "en", StringComparison.OrdinalIgnoreCase);
        HomeNav.Content = en ? "⌂   Home" : "⌂   Главная";
        ClickersNav.Content = en ? "●   Clickers" : "●   Кликеры";
        MacrosNav.Content = en ? "⚡   Macros" : "⚡   Макросы";
        CoordsNav.Content = en ? "⌖   Coordinates" : "⌖   Координаты";
        SettingsNav.Content = en ? "⚙   Settings" : "⚙   Настройки";
        StopHint.Text = en ? "Stop everything" : "Остановить всё";
        HomeTitle.Text = en ? "Home" : "Главная";
        HomeSubtitle.Text = en ? "Quick control of every feature" : "Быстрый контроль всех функций";
        HeroTitle.Text = en ? "Fast. Clean. No clutter." : "Быстро. Чисто. Без лишнего.";
        HeroSubtitle.Text = en ? "Native C# / WPF engine, SendInput and saved settings." : "Нативный C# / WPF движок, SendInput и сохранение настроек.";
        OpenMacrosButton.Content = en ? "Open macros" : "Открыть макросы";
        ClickersTitle.Text = en ? "Clickers" : "Кликеры";
        ClickersSubtitle.Text = en ? "Two independent clickers with separate hotkeys" : "Два независимых кликера с отдельными хоткеями";
        C1HotkeyLabel.Text = C2HotkeyLabel.Text = BpHotkeyLabel.Text = BoltsHotkeyLabel.Text = en ? "Hotkey" : "Хоткей";
        C1ButtonLabel.Text = C2ButtonLabel.Text = en ? "Mouse button" : "Кнопка мыши";
        MacrosTitle.Text = en ? "Macros" : "Макросы";
        MacrosSubtitle.Text = en ? "Both macros can stay enabled at the same time" : "Оба макроса можно держать включёнными одновременно";
        BpSpeedLabel.Text = BoltsSpeedLabel.Text = en ? "Speed" : "Скорость";
        MacroTip.Text = en ? "Keys use SendInput with reliable down/up timing." : "Нажатия отправляются через SendInput с безопасным down/up.";
        CoordsTitle.Text = en ? "Coordinates" : "Координаты";
        CoordsSubtitle.Text = en ? "ARM F6 → point the mouse → press F6" : "ARM F6 → наведи мышь → нажми F6";
        SavedCoordsTitle.Text = en ? "Saved points" : "Сохранённые точки";
        DeleteCoordButton.Content = en ? "Delete" : "Удалить";
        ActiveCoordHint.Text = en ? "Select a point on the left — it becomes the Bolt Push target immediately." : "Выбери точку слева — она сразу станет активной для Bolt Push.";
        WallhopSubtitle.Text = en ? "Two directions like 5.22" : "Две стороны как в 5.22";
        SettingsTitle.Text = en ? "Settings" : "Настройки";
        SettingsSubtitle.Text = en ? "Language, background and app options" : "Язык, фон и параметры программы";
        LanguageLabel.Text = en ? "Interface language" : "Язык интерфейса";
        BackgroundLabel.Text = en ? "Background" : "Фон";
        ChooseBackgroundButton.Content = en ? "Photo / video" : "Фото / видео";
        ClearBackgroundButton.Content = en ? "Clear" : "Очистить";
        SaveButton.Content = en ? "Save settings" : "Сохранить настройки";
        ResetButton.Content = en ? "Reset settings" : "Сбросить настройки";
        UpdateLabels();
        RefreshActiveCoordinate();
    }

    private void UpdateLabels()
    {
        bool en = string.Equals(_settings.Language, "en", StringComparison.OrdinalIgnoreCase);
        C1CpsLabel.Text = $"{(en ? "Speed" : "Скорость")} · {(int)_settings.Clicker1.Cps} CPS";
        C2CpsLabel.Text = $"{(en ? "Speed" : "Скорость")} · {(int)_settings.Clicker2.Cps} CPS";
        WallhopPixelsLabel.Text = $"{(en ? "Turn" : "Поворот")} · {_settings.Wallhop.Pixels} px";
        WallhopDelayLabel.Text = $"{(en ? "Return" : "Возврат")} · {_settings.Wallhop.ReturnDelayMs} ms";
    }

    private void ChooseBackground_Click(object sender, RoutedEventArgs e)
    {
        var dialog = new OpenFileDialog
        {
            Title = "RiuClicker Background",
            Filter = "Image / Video|*.png;*.jpg;*.jpeg;*.bmp;*.gif;*.mp4;*.wmv|Images|*.png;*.jpg;*.jpeg;*.bmp;*.gif|Video|*.mp4;*.wmv"
        };
        if (dialog.ShowDialog() != true) return;
        _settings.BackgroundPath = dialog.FileName;
        BackgroundPathText.Text = dialog.FileName;
        ApplyBackground();
        SaveQuiet();
    }

    private void ClearBackground_Click(object sender, RoutedEventArgs e)
    {
        _settings.BackgroundPath = "";
        BackgroundPathText.Text = "Default";
        ApplyBackground();
        SaveQuiet();
    }

    private void ApplyBackground()
    {
        try
        {
            BackgroundVideo.Stop();
            BackgroundVideo.Source = null;
            BackgroundVideo.Visibility = Visibility.Collapsed;
            BackgroundImage.Source = null;
            BackgroundImage.Visibility = Visibility.Collapsed;

            string path = _settings.BackgroundPath;
            if (string.IsNullOrWhiteSpace(path) || !File.Exists(path)) return;
            string ext = Path.GetExtension(path).ToLowerInvariant();
            if (ext is ".mp4" or ".wmv")
            {
                BackgroundVideo.Source = new Uri(path, UriKind.Absolute);
                BackgroundVideo.Visibility = Visibility.Visible;
                BackgroundVideo.Play();
            }
            else
            {
                var image = new BitmapImage();
                image.BeginInit();
                image.CacheOption = BitmapCacheOption.OnLoad;
                image.UriSource = new Uri(path, UriKind.Absolute);
                image.EndInit();
                image.Freeze();
                BackgroundImage.Source = image;
                BackgroundImage.Visibility = Visibility.Visible;
            }
        }
        catch (Exception ex) { StatusText.Text = "Background: " + ex.Message; }
    }

    private void StartupToast_Changed(object sender, RoutedEventArgs e)
    {
        if (_loading) return;
        _settings.StartupToast = StartupToastCheck.IsChecked == true;
        SaveQuiet();
    }

    private async void ShowStartupToast()
    {
        StartupToast.Visibility = Visibility.Visible;
        StartupToast.BeginAnimation(OpacityProperty, new DoubleAnimation(0, 1, TimeSpan.FromMilliseconds(220)));
        await Task.Delay(2200);
        var fade = new DoubleAnimation(1, 0, TimeSpan.FromMilliseconds(320));
        fade.Completed += (_, _) => StartupToast.Visibility = Visibility.Collapsed;
        StartupToast.BeginAnimation(OpacityProperty, fade);
    }

    private void Save_Click(object sender, RoutedEventArgs e)
    {
        SaveQuiet();
        StatusText.Text = _settings.Language == "en" ? "Settings saved" : "Настройки сохранены";
    }

    private void Reset_Click(object sender, RoutedEventArgs e)
    {
        bool en = _settings.Language == "en";
        var result = MessageBox.Show(en ? "Reset all RiuClicker settings?" : "Сбросить все настройки RiuClicker?", "RiuClicker 1.0", MessageBoxButton.YesNo, MessageBoxImage.Question);
        if (result != MessageBoxResult.Yes) return;
        _engine?.StopAll();
        var defaults = new AppSettings();
        _settings.Clicker1 = defaults.Clicker1;
        _settings.Clicker2 = defaults.Clicker2;
        _settings.BoltPush = defaults.BoltPush;
        _settings.Bolts = defaults.Bolts;
        _settings.Wallhop = defaults.Wallhop;
        _settings.Coordinates = defaults.Coordinates;
        _settings.BoltPushCoordinateId = "";
        _settings.Language = defaults.Language;
        _settings.BackgroundPath = "";
        _settings.StartupToast = true;
        _loading = true;
        ApplySettingsToUi();
        _loading = false;
        ApplyLanguage();
        ApplyBackground();
        SaveQuiet();
        UpdateHomeSummary();
    }

    private void UpdateHomeSummary()
    {
        HomeClicker1.Text = $"{_settings.Clicker1.Hotkey} · {(int)_settings.Clicker1.Cps} CPS";
        HomeClicker2.Text = $"{_settings.Clicker2.Hotkey} · {(int)_settings.Clicker2.Cps} CPS";
        HomeBoltPush.Text = $"{_settings.BoltPush.Hotkey} · V V V → SHIFT";
        HomeBoltPushState.Text = _settings.BoltPush.Enabled ? "READY" : "DISABLED";
        HomeBoltPushState.Foreground = new SolidColorBrush(_settings.BoltPush.Enabled ? Color.FromRgb(97, 231, 178) : Color.FromRgb(255, 118, 139));
        HomeWallhop.Text = $"{_settings.Wallhop.LeftHotkey} LEFT · {_settings.Wallhop.RightHotkey} RIGHT";
        UpdateFeatureState("clicker1", _engine?.Clicker1Active == true);
        UpdateFeatureState("clicker2", _engine?.Clicker2Active == true);
    }

    private void SaveQuiet()
    {
        try { _settings.Save(); } catch (Exception ex) { StatusText.Text = "Save: " + ex.Message; }
    }

    private void TitleBar_MouseLeftButtonDown(object sender, MouseButtonEventArgs e)
    {
        if (e.ButtonState == MouseButtonState.Pressed)
            try { DragMove(); } catch { }
    }

    private void Minimize_Click(object sender, RoutedEventArgs e) => WindowState = WindowState.Minimized;
    private void Close_Click(object sender, RoutedEventArgs e) => Close();

    protected override void OnClosing(CancelEventArgs e)
    {
        SaveQuiet();
        base.OnClosing(e);
    }

    protected override void OnClosed(EventArgs e)
    {
        if (_engine is not null) _ = _engine.DisposeAsync();
        base.OnClosed(e);
    }
}
