from pathlib import Path

root = Path('src')

# MainWindow.xaml: video background layer, refreshed background card, uninstall card, version.
p = root / 'MainWindow.xaml'
s = p.read_text(encoding='utf-8')
img = '<Image x:Name="BackgroundImage" Stretch="UniformToFill" Opacity="1" Visibility="Collapsed"/>'
media = '''<Image x:Name="BackgroundImage" Stretch="UniformToFill" Opacity="1" Visibility="Collapsed"/>
        <MediaElement x:Name="BackgroundVideo" Stretch="UniformToFill" Opacity="1" Visibility="Collapsed"
                      LoadedBehavior="Manual" UnloadedBehavior="Manual" IsMuted="True" ScrubbingEnabled="True"
                      MediaEnded="BackgroundVideo_MediaEnded" MediaFailed="BackgroundVideo_MediaFailed"/>'''
if img not in s:
    raise SystemExit('BackgroundImage target not found')
s = s.replace(img, media, 1)
s = s.replace('ФОНОВОЕ ИЗОБРАЖЕНИЕ', 'ФОН · ФОТО И ВИДЕО')
s = s.replace('ВЫБРАТЬ ФОТО', 'ВЫБРАТЬ ФОТО / ВИДЕО')
s = s.replace('Где показывать фото', 'Где показывать фон')
s = s.replace('Режим слабого ПК отключает RGB и фоновое фото, но не меняет работу кликов и макросов.', 'Режим слабого ПК отключает RGB и фоновое фото/видео, но не меняет работу кликов и макросов.')
needle = '<Button Content="СБРОСИТЬ ВСЕ НАСТРОЙКИ" Style="{StaticResource DangerButton}" Margin="0,7,0,0" Click="ResetSettings_Click"/></StackPanel></Border></StackPanel>'
uninstall_card = '<Button Content="СБРОСИТЬ ВСЕ НАСТРОЙКИ" Style="{StaticResource DangerButton}" Margin="0,7,0,0" Click="ResetSettings_Click"/></StackPanel></Border><Border Style="{StaticResource CardBorder}" Margin="0,10,0,0"><StackPanel><TextBlock Text="УДАЛЕНИЕ RIU" FontWeight="Bold" Foreground="#FF6B7A"/><TextBlock Text="Покажет найденные старые Riu/Strawberry-файлы и текущую версию. Ничего не удаляется без подтверждения." Foreground="{DynamicResource MutedBrush}" FontSize="10" TextWrapping="Wrap" Margin="0,5,0,9"/><Button Content="УДАЛИТЬ RIU CLICKER С ЭТОГО ПК" Style="{StaticResource DangerButton}" Click="UninstallRiu_Click"/></StackPanel></Border></StackPanel>'
if needle not in s:
    raise SystemExit('Settings uninstall insertion target not found')
s = s.replace(needle, uninstall_card, 1)
# Version + CPS slider visible range. The input auto-expands beyond this value via CPS hotfix.
s = s.replace('Maximum="500" ValueChanged="CpsSlider_Changed"', 'Maximum="5000" ValueChanged="CpsSlider_Changed"')
s = s.replace('5.20', '5.22')
p.write_text(s, encoding='utf-8')

# MainWindow.Extras.cs: media picker/playback + confirmed uninstall.
p = root / 'MainWindow.Extras.cs'
s = p.read_text(encoding='utf-8')
old_filter = 'var dialog = new OpenFileDialog { Filter = T("Изображения") + "|*.png;*.jpg;*.jpeg;*.bmp;*.webp|" + T("Все файлы") + "|*.*" };'
new_filter = '''var dialog = new OpenFileDialog
        {
            Filter = T("Фото и видео") + "|*.png;*.jpg;*.jpeg;*.bmp;*.webp;*.mp4;*.m4v;*.mov;*.avi;*.wmv|" +
                     T("Изображения") + "|*.png;*.jpg;*.jpeg;*.bmp;*.webp|" +
                     T("Видео") + "|*.mp4;*.m4v;*.mov;*.avi;*.wmv|" + T("Все файлы") + "|*.*"
        };'''
if old_filter not in s:
    raise SystemExit('Background picker filter target not found')
s = s.replace(old_filter, new_filter, 1)
old_clear = '_settings.Appearance.BackgroundImagePath = ""; BackgroundPathText.Text = T("Не выбрано"); ApplyAppearance(); Save();'
new_clear = 'try { BackgroundVideo.Stop(); BackgroundVideo.Source = null; } catch { }\n        _settings.Appearance.BackgroundImagePath = ""; BackgroundPathText.Text = T("Не выбрано"); ApplyAppearance(); Save();'
if old_clear not in s:
    raise SystemExit('Clear background target not found')
s = s.replace(old_clear, new_clear, 1)
preview_marker = '    private async void PreviewIntro_Click(object sender, RoutedEventArgs e)'
handlers = '''    private static bool IsVideoBackground(string path)
    {
        var ext = Path.GetExtension(path).ToLowerInvariant();
        return ext is ".mp4" or ".m4v" or ".mov" or ".avi" or ".wmv";
    }

    private void BackgroundVideo_MediaEnded(object sender, RoutedEventArgs e)
    {
        try { BackgroundVideo.Position = TimeSpan.Zero; BackgroundVideo.Play(); } catch { }
    }

    private void BackgroundVideo_MediaFailed(object sender, ExceptionRoutedEventArgs e)
    {
        BackgroundVideo.Visibility = Visibility.Collapsed;
        Log("Видео-фон не удалось воспроизвести: " + e.ErrorException?.Message);
    }

'''
if preview_marker not in s:
    raise SystemExit('Preview marker not found')
s = s.replace(preview_marker, handlers + preview_marker, 1)

start_text = '        if (!a.LowEndMode && !string.IsNullOrWhiteSpace(a.BackgroundImagePath) && File.Exists(a.BackgroundImagePath))'
start = s.find(start_text)
if start < 0:
    raise SystemExit('ApplyAppearance background block start not found')
end = s.find('\n\n        if (a.LowEndMode)', start)
if end < 0:
    raise SystemExit('ApplyAppearance background block end not found')
new_block = '''        try { BackgroundVideo.Stop(); } catch { }
        BackgroundVideo.Visibility = Visibility.Collapsed;
        BackgroundImage.Visibility = Visibility.Collapsed;

        if (!a.LowEndMode && !string.IsNullOrWhiteSpace(a.BackgroundImagePath) && File.Exists(a.BackgroundImagePath))
        {
            try
            {
                var stretch = a.BackgroundFit switch { "stretch" => Stretch.Fill, "contain" => Stretch.Uniform, _ => Stretch.UniformToFill };
                if (IsVideoBackground(a.BackgroundImagePath))
                {
                    BackgroundVideo.Source = new Uri(a.BackgroundImagePath, UriKind.Absolute);
                    BackgroundVideo.Stretch = stretch;
                    BackgroundVideo.IsMuted = true;
                    BackgroundVideo.Volume = 0;
                    BackgroundVideo.Position = TimeSpan.Zero;
                    BackgroundVideo.Visibility = Visibility.Visible;
                    BackgroundVideo.Play();
                    TitleBarBorder.Background = (Brush)Application.Current.Resources["SidebarBrush"];
                    PageHeaderPanel.Background = Brushes.Transparent;
                }
                else
                {
                    var bmp = new BitmapImage();
                    bmp.BeginInit(); bmp.CacheOption = BitmapCacheOption.OnLoad; bmp.UriSource = new Uri(a.BackgroundImagePath, UriKind.Absolute); bmp.EndInit();
                    BackgroundImage.Source = bmp;
                    BackgroundImage.Stretch = stretch;
                    if (a.BackgroundMode == "headers")
                    {
                        var brush = new ImageBrush(bmp)
                        {
                            Stretch = stretch,
                            Opacity = Math.Clamp(1.0 - a.OverlayOpacity / 120.0, .12, .75)
                        };
                        TitleBarBorder.Background = brush;
                        PageHeaderPanel.Background = brush;
                    }
                    else
                    {
                        BackgroundImage.Visibility = Visibility.Visible;
                        TitleBarBorder.Background = (Brush)Application.Current.Resources["SidebarBrush"];
                        PageHeaderPanel.Background = Brushes.Transparent;
                    }
                }
            }
            catch
            {
                BackgroundImage.Visibility = Visibility.Collapsed;
                BackgroundVideo.Visibility = Visibility.Collapsed;
            }
        }
        else
        {
            BackgroundImage.Visibility = Visibility.Collapsed;
            BackgroundVideo.Visibility = Visibility.Collapsed;
            TitleBarBorder.Background = (Brush)Application.Current.Resources["SidebarBrush"];
            PageHeaderPanel.Background = Brushes.Transparent;
        }'''
s = s[:start] + new_block + s[end:]
s = s.replace('if (a.LowEndMode) { _rgbTimer.Stop(); BackgroundImage.Visibility = Visibility.Collapsed; }', 'if (a.LowEndMode) { _rgbTimer.Stop(); BackgroundImage.Visibility = Visibility.Collapsed; BackgroundVideo.Visibility = Visibility.Collapsed; try { BackgroundVideo.Stop(); } catch { } }')

clear_log_marker = '    private void ClearLog_Click(object sender, RoutedEventArgs e)'
uninstall_method = r'''    private void UninstallRiu_Click(object sender, RoutedEventArgs e)
    {
        try
        {
            var currentExe = Environment.ProcessPath;
            if (string.IsNullOrWhiteSpace(currentExe)) return;
            var roots = new HashSet<string>(StringComparer.OrdinalIgnoreCase)
            {
                AppContext.BaseDirectory,
                Environment.GetFolderPath(Environment.SpecialFolder.DesktopDirectory),
                Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), "Downloads")
            };
            var patterns = new[]
            {
                "RiuClicker*.exe", "StrawberryClicker*.exe",
                "Riu-and-Strawberry*.zip", "Riu-Strawberry*-Source.zip"
            };
            var files = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
            foreach (var root in roots.Where(Directory.Exists))
            {
                foreach (var pattern in patterns)
                {
                    try { foreach (var file in Directory.EnumerateFiles(root, pattern, SearchOption.TopDirectoryOnly)) files.Add(Path.GetFullPath(file)); }
                    catch { }
                }
            }
            files.Add(Path.GetFullPath(currentExe));
            var preview = string.Join(Environment.NewLine, files.Take(12).Select(Path.GetFileName));
            if (files.Count > 12) preview += $"{Environment.NewLine}…и ещё {files.Count - 12}";
            var answer = MessageBox.Show(this,
                $"Будут удалены только найденные файлы Riu/Strawberry Clicker и текущая версия ({files.Count}):\n\n{preview}\n\nПродолжить?",
                "Удаление Riu Clicker", MessageBoxButton.YesNo, MessageBoxImage.Warning);
            if (answer != MessageBoxResult.Yes) return;
            StopAll();
            try { BackgroundVideo.Stop(); } catch { }
            var script = Path.Combine(Path.GetTempPath(), $"riu-uninstall-{Guid.NewGuid():N}.cmd");
            var lines = new List<string> { "@echo off", "timeout /t 2 /nobreak >nul" };
            foreach (var file in files) lines.Add($"del /f /q \"{file.Replace("\"", "\"\"")}\" >nul 2>&1");
            lines.Add("del /f /q \"%~f0\" >nul 2>&1");
            File.WriteAllLines(script, lines, System.Text.Encoding.ASCII);
            Process.Start(new ProcessStartInfo { FileName = script, UseShellExecute = true, WindowStyle = ProcessWindowStyle.Hidden });
            Application.Current.Shutdown();
        }
        catch (Exception ex) { MessageBox.Show(this, ex.Message, "Riu Clicker", MessageBoxButton.OK, MessageBoxImage.Error); }
    }

'''
if clear_log_marker not in s:
    raise SystemExit('ClearLog marker not found')
s = s.replace(clear_log_marker, uninstall_method + clear_log_marker, 1)
s = s.replace('5.20', '5.22')
p.write_text(s, encoding='utf-8')

# Stop background video on window closing + version bump.
p = root / 'MainWindow.xaml.cs'
s = p.read_text(encoding='utf-8')
if 'try { BackgroundVideo.Stop(); } catch { }' not in s:
    s = s.replace('        _input.Dispose();', '        try { BackgroundVideo.Stop(); } catch { }\n        _input.Dispose();', 1)
s = s.replace('5.20', '5.22')
p.write_text(s, encoding='utf-8')

# Bump remaining version-bearing source files to 5.22.
for p in root.rglob('*'):
    if p.is_file() and p.suffix.lower() in {'.cs', '.xaml', '.csproj'}:
        text = p.read_text(encoding='utf-8')
        text = text.replace('5.20', '5.22').replace('5.21', '5.22')
        p.write_text(text, encoding='utf-8')

print('Applied Riu Clicker 5.22 UI/video/uninstall patch')
