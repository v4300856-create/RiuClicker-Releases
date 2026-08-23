from pathlib import Path

root=Path('src')

def rw(name):
    p=root/name
    return p, p.read_text(encoding='utf-8')

def save(p,s): p.write_text(s,encoding='utf-8')

# Models / branding / force English
p,s=rw('Models.cs')
s=s.replace('public string Language { get; set; } = "ru";', 'public string Language { get; set; } = "en";')
s=s.replace('public const string Name = "Riu Clicker";', 'public const string Name = "Free RiuClicker";')
s=s.replace('public const string SettingsFolder = "RiuClickerCS";', 'public const string SettingsFolder = "FreeRiuClicker";')
s=s.replace('public const string DefaultIntro = "xDragonsx on top";', 'public const string DefaultIntro = "Free RiuClicker";')
s=s.replace('''    public static void ApplyDefaults(AppSettings s)\n    {\n        if (!IsStrawberry) return;''','''    public static void ApplyDefaults(AppSettings s)\n    {\n        s.Appearance.Language = "en";\n        if (!IsStrawberry) return;''')
save(p,s)

# Localization is permanently English in free build
p,s=rw('Localization.cs')
s=s.replace('public static string CurrentLanguage { get; private set; } = "ru";', 'public static string CurrentLanguage { get; private set; } = "en";')
old='''    public static void SetLanguage(string? code)\n    {\n        CurrentLanguage = Languages.Any(x => string.Equals(x.Code, code, StringComparison.OrdinalIgnoreCase)) ? code! : "ru";\n    }'''
if old in s:
    s=s.replace(old,'''    public static void SetLanguage(string? code)\n    {\n        CurrentLanguage = "en";\n    }''')
else:
    import re
    s=re.sub(r'public static void SetLanguage\(string\? code\)\s*\{.*?\n\s*\}', 'public static void SetLanguage(string? code)\n    {\n        CurrentLanguage = "en";\n    }', s, count=1, flags=re.S)
save(p,s)

# Branding labels
p,s=rw('BrandVisual.cs')
s=s.replace('Title = $"{BrandInfo.Name} 5.22 · Nova Control";', 'Title = "Free RiuClicker";')
s=s.replace('var name = BrandInfo.IsStrawberry ? "STRAWBERRY CLICKER" : "RIU CLICKER";', 'var name = "FREE RIUCLICKER";')
s=s.replace('HeaderBrandVersionText.Text = "NOVA CONTROL  •  5.22";', 'HeaderBrandVersionText.Text = "FREE EDITION";')
s=s.replace('SidebarBrandVersionText.Text = "5.22  •  NOVA CONTROL";', 'SidebarBrandVersionText.Text = "FREE  •  RIUCLICKER";')
s=s.replace('SidebarBrandVisualHint.Text = BrandInfo.IsStrawberry ? "3D · STRAWBERRY" : "3D · RIU";', 'SidebarBrandVisualHint.Text = "3D · FREE";')
save(p,s)

# Disable wallhop runtime, force English each launch, remove wallhop dashboard updates/conflicts
p,s=rw('MainWindow.xaml.cs')
s=s.replace('''    private async void Window_Loaded(object sender, RoutedEventArgs e)\n    {\n        LoadUiFromSettings();''','''    private async void Window_Loaded(object sender, RoutedEventArgs e)\n    {\n        _settings.Appearance.Language = "en";\n        _settings.Wallhop.Hotkey = "";\n        Localization.SetLanguage("en");\n        LoadUiFromSettings();''')
s=s.replace('        PageWallhop.Visibility = page == "Wallhop" ? Visibility.Visible : Visibility.Collapsed;', '        PageWallhop.Visibility = Visibility.Collapsed;')
s=s.replace('            "Wallhop" => (T("ВОЛЛХОП"), T("Только поворот камеры — движение остаётся за тобой")),\n','')
s=s.replace('        HomeWallhopState.Text = "● " + T(Volatile.Read(ref _wallhopRunning) != 0 ? (Volatile.Read(ref _wallhopQueued) != 0 ? "ОЧЕРЕДЬ" : "РАБОТАЕТ") : "ГОТОВ");\n        HomeWallhopState.Foreground = Volatile.Read(ref _wallhopRunning) != 0 ? (Brush)FindResource("AccentBrush") : (Brush)FindResource("SuccessBrush");\n        HomeWallhopMeta.Text = $"{_settings.Wallhop.Hotkey} · {_settings.Wallhop.FlickPixels}px · {_settings.Wallhop.SmoothSteps} {T("пакет.")} · {T(_settings.Wallhop.ReturnCamera ? "возврат" : "без возврата")}";\n','')
s=s.replace('        Add(_settings.Wallhop.Hotkey, "Wallhop");\n','')
s=s.replace('        LoadWallhopUi();\n','')
save(p,s)

# Disable wallhop hotkey capture and remove turbo/instant macro modes
p,s=rw('MainWindow.Extras.cs')
s=s.replace('''        if (string.Equals(_settings.Wallhop.Hotkey, key, StringComparison.OrdinalIgnoreCase))\n        {\n            StartWallhop();\n            return;\n        }\n''','')
s=s.replace('        else if (target == "wallhop") _settings.Wallhop.Hotkey = key;\n','')
s=s.replace('        Check(_settings.Wallhop.Hotkey, "Wallhop", target == "wallhop");\n','')
s=s.replace('''    private void MacroPreset_Click(object sender, RoutedEventArgs e)\n    {\n        if (sender is not Button b) return;\n        var m = SelectedMacroFromList(); if (m is null) return;\n        MacroEngine.ApplySpeedPreset(m, b.Tag?.ToString() ?? "fast");\n        _initializing = true; RefreshMacroEditor(m); _initializing = false; Save();\n    }''','''    private void MacroPreset_Click(object sender, RoutedEventArgs e)\n    {\n        if (sender is not Button b) return;\n        var m = SelectedMacroFromList(); if (m is null) return;\n        var mode = b.Tag?.ToString() ?? "fast";\n        if (mode is not ("stable" or "fast")) mode = "fast";\n        MacroEngine.ApplySpeedPreset(m, mode);\n        _initializing = true; RefreshMacroEditor(m); _initializing = false; Save();\n    }''')
s=s.replace('        _settings.Appearance.Language = SelectedTag(LanguageBox, "ru");\n        ApplyLanguage(); Save();', '        _settings.Appearance.Language = "en";\n        ApplyLanguage(); Save();')
s=s.replace('        Localization.SetLanguage(_settings.Appearance.Language);', '        _settings.Appearance.Language = "en";\n        Localization.SetLanguage("en");')
s=s.replace('                "Macros" => "◆   " + T("МАКРОСЫ"), "Wallhop" => "↗   " + T("ВОЛЛХОП"), "Profiles" => "▦   " + T("ПРОФИЛИ"),', '                "Macros" => "◆   " + T("МАКРОСЫ"), "Profiles" => "▦   " + T("ПРОФИЛИ"),')
s=s.replace('        RefreshClickerRuntime(1); RefreshClickerRuntime(2); RefreshCoordinateEditor(); RefreshMacroEditor(); LoadWallhopUi();', '        RefreshClickerRuntime(1); RefreshClickerRuntime(2); RefreshCoordinateEditor(); RefreshMacroEditor();')
s=s.replace('        SelectComboByTag(LanguageBox, a.Language);', '        _settings.Appearance.Language = "en";\n        SelectComboByTag(LanguageBox, "en");')
save(p,s)

# Engine allows only stable/fast presets
p,s=rw('Engines.cs')
s=s.replace('''        m.SpeedMode = mode;\n        (m.KeyHoldMs, m.ModifierHoldMs, m.StepGapMs, m.PointerSettleMs) = mode switch\n        {\n            "stable" => (35, 90, 55, 40),\n            "turbo" => (4, 12, 2, 4),\n            "instant" => (1, 5, 0, 1),\n            _ => (12, 35, 8, 12)\n        };''','''        mode = mode == "stable" ? "stable" : "fast";\n        m.SpeedMode = mode;\n        (m.KeyHoldMs, m.ModifierHoldMs, m.StepGapMs, m.PointerSettleMs) = mode switch\n        {\n            "stable" => (35, 90, 55, 40),\n            _ => (12, 35, 8, 12)\n        };''')
save(p,s)

# XAML: no wallhop navigation, only 2 macro presets, English-only language, free branding
p,s=rw('MainWindow.xaml')
s=s.replace('Text="RIU CLICKER"', 'Text="FREE RIUCLICKER"')
s=s.replace('Text="5.22  •  NOVA CONTROL"', 'Text="FREE  •  RIUCLICKER"')
s=s.replace('<Button Content="↗   Wallhop" Tag="Wallhop" Style="{StaticResource NavButton}" Click="Nav_Click"/>', '')
s=s.replace('<Border Grid.Column="0" Style="{StaticResource CardBorder}">\n                                        <StackPanel>\n                                            <Grid><TextBlock Text="WALLHOP" FontWeight="Bold" Foreground="{DynamicResource AccentBrush}"/><TextBlock x:Name="HomeWallhopState" Text="● ГОТОВ" HorizontalAlignment="Right" FontWeight="Bold"/></Grid>', '<Border Grid.Column="0" Style="{StaticResource CardBorder}" Visibility="Collapsed">\n                                        <StackPanel>\n                                            <Grid><TextBlock Text="WALLHOP" FontWeight="Bold" Foreground="{DynamicResource AccentBrush}"/><TextBlock x:Name="HomeWallhopState" Text="● READY" HorizontalAlignment="Right" FontWeight="Bold"/></Grid>')
s=s.replace('<Grid x:Name="PageWallhop" Visibility="Collapsed">', '<Grid x:Name="PageWallhop" Visibility="Collapsed" IsEnabled="False">')
old='''<Grid Margin="0,10,0,0"><Grid.ColumnDefinitions><ColumnDefinition/><ColumnDefinition/><ColumnDefinition/><ColumnDefinition/></Grid.ColumnDefinitions><Button Content="НАДЁЖНО" Style="{StaticResource RiuButton}" Margin="2" Click="MacroPreset_Click" Tag="stable"/><Button Grid.Column="1" Content="БЫСТРО" Style="{StaticResource RiuButton}" Margin="2" Click="MacroPreset_Click" Tag="fast"/><Button Grid.Column="2" Content="ТУРБО" Style="{StaticResource RiuButton}" Margin="2" Click="MacroPreset_Click" Tag="turbo"/><Button Grid.Column="3" Content="МГНОВЕННО" Style="{StaticResource RiuButton}" Margin="2" Click="MacroPreset_Click" Tag="instant"/></Grid>'''
new='''<Grid Margin="0,10,0,0"><Grid.ColumnDefinitions><ColumnDefinition/><ColumnDefinition/></Grid.ColumnDefinitions><Button Content="STABLE" Style="{StaticResource RiuButton}" Margin="2" Click="MacroPreset_Click" Tag="stable"/><Button Grid.Column="1" Content="FAST" Style="{StaticResource RiuButton}" Margin="2" Click="MacroPreset_Click" Tag="fast"/></Grid>'''
if old not in s: raise SystemExit('macro preset XAML target not found')
s=s.replace(old,new)
old_lang='''<StackPanel Margin="0,0,6,0"><TextBlock Text="Язык / Language" Foreground="{DynamicResource MutedBrush}"/><ComboBox x:Name="LanguageBox" Style="{StaticResource RiuComboBox}" SelectionChanged="Language_Changed"><ComboBoxItem Content="Русский" Tag="ru"/><ComboBoxItem Content="English" Tag="en"/><ComboBoxItem Content="Українська" Tag="uk"/><ComboBoxItem Content="简体中文" Tag="zh-CN"/><ComboBoxItem Content="Deutsch" Tag="de"/><ComboBoxItem Content="Español" Tag="es"/><ComboBoxItem Content="Français" Tag="fr"/><ComboBoxItem Content="Polski" Tag="pl"/></ComboBox></StackPanel>'''
new_lang='''<StackPanel Margin="0,0,6,0"><TextBlock Text="Language" Foreground="{DynamicResource MutedBrush}"/><ComboBox x:Name="LanguageBox" Style="{StaticResource RiuComboBox}" IsEnabled="False" SelectionChanged="Language_Changed"><ComboBoxItem Content="English" Tag="en"/></ComboBox></StackPanel>'''
if old_lang not in s: raise SystemExit('language XAML target not found')
s=s.replace(old_lang,new_lang)
s=s.replace('<Button Content="НАСТРОИТЬ WALLHOP" Tag="Wallhop" Style="{StaticResource RiuButton}" Click="DashboardNavigate_Click"/>', '<TextBlock Text="Free edition" Foreground="{DynamicResource MutedBrush}"/>')
s=s.replace('Text="RIU CLICKER · C# FULL"', 'Text="FREE RIUCLICKER"')
s=s.replace('Text="Riu Clicker 5.22: Nova Control Center, проверка конфликтов хоткеев, профили двух кликеров, резервные копии, точный таймер и wallhop-очередь."', 'Text="Free RiuClicker: auto clicker, coordinates, profiles, macros and precise timing."')
s=s.replace('Text="F8 — кликер 1   ·   F9 — кликер 2   ·   F7 — поворот камеры   ·   F12 — остановить всё"', 'Text="F8 — Clicker 1   ·   F9 — Clicker 2   ·   F12 — Stop All"')
s=s.replace('Text="Mouse4 / Mouse5 можно назначать для запуска кликеров, макросов и воллхопа. Синтетические клавиши из макроса не запускают горячие клавиши повторно."', 'Text="Mouse4 / Mouse5 can be assigned to clickers and macros. Synthetic macro input never retriggers hotkeys."')
save(p,s)

# project version
p,s=rw('RiuClickerCS.csproj')
s=s.replace('<Version>5.22.0</Version>','<Version>1.0.0</Version>')
s=s.replace('<AssemblyVersion>5.22.0.0</AssemblyVersion>','<AssemblyVersion>1.0.0.0</AssemblyVersion>')
s=s.replace('<FileVersion>5.22.0.0</FileVersion>','<FileVersion>1.0.0.0</FileVersion>')
save(p,s)

print('Free RiuClicker patch applied')
