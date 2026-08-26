from pathlib import Path

root = Path('src')

(root / 'StartupBannerWindow.xaml').write_text('''<Window x:Class="RiuClickerCS.StartupBannerWindow"
        xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
        xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
        Width="520" Height="180" WindowStartupLocation="CenterScreen"
        WindowStyle="None" ResizeMode="NoResize" AllowsTransparency="True"
        Background="Transparent" ShowInTaskbar="False" Topmost="True">
    <Border Background="#EE080A12" BorderBrush="#7C3AED" BorderThickness="1.5" CornerRadius="22" Padding="28">
        <Grid>
            <StackPanel VerticalAlignment="Center" HorizontalAlignment="Center">
                <TextBlock Text="xDragonsx on top" Foreground="White" FontSize="32" FontWeight="Bold" HorizontalAlignment="Center"/>
                <TextBlock Text="RIUCLICKER" Foreground="#22D3EE" FontSize="12" FontWeight="SemiBold" Margin="0,10,0,0" HorizontalAlignment="Center"/>
            </StackPanel>
        </Grid>
    </Border>
</Window>
''', encoding='utf-8')

(root / 'StartupBannerWindow.xaml.cs').write_text('''using System.Windows;\n\nnamespace RiuClickerCS;\n\npublic partial class StartupBannerWindow : Window\n{\n    public StartupBannerWindow()\n    {\n        InitializeComponent();\n    }\n}\n''', encoding='utf-8')

app = root / 'App.xaml.cs'
s = app.read_text(encoding='utf-8')
needle = '        base.OnStartup(e);\n        ShutdownMode = ShutdownMode.OnExplicitShutdown;'
replacement = '''        base.OnStartup(e);\n        ShutdownMode = ShutdownMode.OnExplicitShutdown;\n\n        // Guaranteed startup banner on every launch.\n        var startupBanner = new StartupBannerWindow();\n        startupBanner.Show();\n        startupBanner.Activate();\n        await Task.Delay(1400);\n        startupBanner.Close();'''
if needle not in s:
    raise SystemExit('App startup marker missing')
s = s.replace(needle, replacement, 1)
app.write_text(s, encoding='utf-8')

print('Applied guaranteed xDragonsx on top startup banner')
