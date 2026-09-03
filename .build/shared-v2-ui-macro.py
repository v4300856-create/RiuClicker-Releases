from pathlib import Path
import re

root=Path('src')

# ---- Macro page: keep the original 5.22 editor/engine, but make timing controls obvious. ----
p=root/'MainWindow.xaml'
s=p.read_text(encoding='utf-8')
repls={
    'Text="Клавиша, мс"':'Text="KEY HOLD · мс"',
    'Text="SHIFT/CTRL/ALT"':'Text="MODIFIER HOLD · мс"',
    'Text="Между шагами"':'Text="STEP GAP · мс"',
    'Text="Перед кликом"':'Text="POINTER SETTLE · мс"',
    'Text="Старт, мс"':'Text="START DELAY · мс"',
    'Text="Повторов"':'Text="REPEAT COUNT"',
    'Text="Между повторами"':'Text="REPEAT DELAY · мс"',
    'Text="Запись 5.22 автоматически сохраняет реальные паузы между нажатиями."':'Text="Запись сама сохраняет реальные паузы. Любую цифру задержки можно изменить вручную."',
    'Text="ФИНАЛЬНЫЙ КЛИК"':'Text="ФИНАЛЬНЫЙ КЛИК · НЕОБЯЗАТЕЛЬНО"',
}
for a,b in repls.items(): s=s.replace(a,b)
# Give layout columns names so the three launch-selected interfaces can really differ.
s=s.replace('<Grid.ColumnDefinitions><ColumnDefinition Width="232"/><ColumnDefinition Width="*"/></Grid.ColumnDefinitions>',
            '<Grid.ColumnDefinitions><ColumnDefinition x:Name="SidebarColumn" Width="232"/><ColumnDefinition Width="*"/></Grid.ColumnDefinitions>',1)
s=s.replace('<Grid Grid.Column="1" Margin="24,18,24,20">',
            '<Grid x:Name="MainContentArea" Grid.Column="1" Margin="24,18,24,20">',1)
p.write_text(s,encoding='utf-8')

# Macro start notification in the normal status/log area.
p=root/'Engines.cs'
s=p.read_text(encoding='utf-8')
needle='''        RunningChanged?.Invoke(macro.Id, true);\n        _ = Task.Run(() => RunOwned(macro, settings, cts));'''
if needle in s and 'Макрос «{macro.Name}» запущен' not in s:
    s=s.replace(needle,'''        RunningChanged?.Invoke(macro.Id, true);\n        Message?.Invoke($"Макрос «{macro.Name}» запущен");\n        _ = Task.Run(() => RunOwned(macro, settings, cts));''',1)
p.write_text(s,encoding='utf-8')

# ---- Three genuinely different interface modes. ----
(root/'InterfacePickerWindow.xaml').write_text(r'''<Window x:Class="RiuClickerCS.InterfacePickerWindow"
 xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
 xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
 Title="RiuClicker · Interface" Width="760" Height="430" WindowStartupLocation="CenterScreen"
 ResizeMode="NoResize" Background="#070A10" Foreground="#F8FAFC">
 <Grid Margin="28">
  <Grid.RowDefinitions><RowDefinition Height="Auto"/><RowDefinition Height="*"/><RowDefinition Height="Auto"/></Grid.RowDefinitions>
  <StackPanel>
   <TextBlock Text="RIUCLICKER" Foreground="#22D3EE" FontWeight="Bold" FontSize="12"/>
   <TextBlock Text="ВЫБЕРИ ИНТЕРФЕЙС" FontSize="30" FontWeight="Black" Margin="0,6,0,4"/>
   <TextBlock Text="Выбор появляется при каждом запуске." Foreground="#94A3B8"/>
  </StackPanel>
  <UniformGrid Grid.Row="1" Columns="3" Margin="0,24,0,20">
   <Button Tag="classic" Click="Pick_Click" Margin="6" Padding="14" Background="#111827" Foreground="White" BorderBrush="#334155">
    <StackPanel><TextBlock Text="CLASSIC" FontSize="18" FontWeight="Bold"/><TextBlock Text="Оригинальный 5.22\nширокое меню\nбирюзовый акцент" Margin="0,12,0,0" Foreground="#94A3B8" TextWrapping="Wrap"/></StackPanel>
   </Button>
   <Button Tag="compact" Click="Pick_Click" Margin="6" Padding="14" Background="#0B1220" Foreground="White" BorderBrush="#22D3EE">
    <StackPanel><TextBlock Text="COMPACT" FontSize="18" FontWeight="Bold"/><TextBlock Text="Узкое меню\nкороткие названия\nбольше места макросам" Margin="0,12,0,0" Foreground="#94A3B8" TextWrapping="Wrap"/></StackPanel>
   </Button>
   <Button Tag="neon" Click="Pick_Click" Margin="6" Padding="14" Background="#170D24" Foreground="White" BorderBrush="#A855F7">
    <StackPanel><TextBlock Text="NEON" FontSize="18" FontWeight="Bold" Foreground="#C084FC"/><TextBlock Text="Фиолетовый стиль\nширокое окно\nкрупнее панели" Margin="0,12,0,0" Foreground="#B9A7C9" TextWrapping="Wrap"/></StackPanel>
   </Button>
  </UniformGrid>
  <TextBlock Grid.Row="2" Text="Можно выбрать другой стиль при следующем запуске" Foreground="#64748B" HorizontalAlignment="Center"/>
 </Grid>
</Window>''',encoding='utf-8')

(root/'InterfacePickerWindow.xaml.cs').write_text(r'''using System.Windows;
namespace RiuClickerCS;
public partial class InterfacePickerWindow : Window
{
    public string SelectedMode { get; private set; } = "classic";
    public InterfacePickerWindow(){InitializeComponent();}
    private void Pick_Click(object sender,RoutedEventArgs e)
    {
        if(sender is FrameworkElement f && f.Tag is string mode) SelectedMode=mode;
        DialogResult=true; Close();
    }
}
''',encoding='utf-8')

(root/'UiModeService.cs').write_text(r'''using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
namespace RiuClickerCS;
public static class UiModeService
{
    static SolidColorBrush B(byte r,byte g,byte b)=>new(Color.FromRgb(r,g,b));
    public static void Apply(MainWindow w,string mode)
    {
        mode=(mode??"classic").ToLowerInvariant();
        if(mode=="compact")
        {
            w.Width=1080; w.Height=730; w.SidebarColumn.Width=new GridLength(172);
            w.MainContentArea.Margin=new Thickness(14,12,14,14);
            Application.Current.Resources["AccentBrush"]=B(34,211,238);
            Application.Current.Resources["WindowBrush"]=B(5,9,15);
            Application.Current.Resources["SidebarBrush"]=B(7,12,20);
            Application.Current.Resources["CardBrush"]=B(12,20,31);
            foreach(var b in w.NavPanel.Children.OfType<Button>())
                b.Content=(b.Tag?.ToString()) switch {"Home"=>"⌂ HOME","Clicker"=>"⚡ CLICK","Wallhop"=>"↗ WALL","Macros"=>"◆ MACRO","Settings"=>"⚙ SET","Coordinates"=>"◎ COORD","Profiles"=>"▦ PROF","Log"=>"≡ LOG","Help"=>"? HELP","Lobby"=>"◉ LOBBY",_=>b.Content};
        }
        else if(mode=="neon")
        {
            w.Width=1320; w.Height=860; w.SidebarColumn.Width=new GridLength(252);
            w.MainContentArea.Margin=new Thickness(34,24,34,28);
            Application.Current.Resources["AccentBrush"]=B(192,132,252);
            Application.Current.Resources["WindowBrush"]=B(10,5,17);
            Application.Current.Resources["SidebarBrush"]=B(16,8,27);
            Application.Current.Resources["CardBrush"]=B(25,14,39);
            Application.Current.Resources["ControlBrush"]=B(34,20,50);
            Application.Current.Resources["LineBrush"]=B(82,52,111);
        }
        else
        {
            w.Width=1180; w.Height=790; w.SidebarColumn.Width=new GridLength(232);
            w.MainContentArea.Margin=new Thickness(24,18,24,20);
        }
    }
}
''',encoding='utf-8')

# Add picker before opening the main window. Works with FREE App.OpenMainWindow and PRO App.OpenMain.
p=root/'App.xaml.cs'
s=p.read_text(encoding='utf-8')
if 'new InterfacePickerWindow()' not in s:
    # FREE helper
    old='''    private void OpenMainWindow()\n    {\n        var main = new MainWindow();\n        MainWindow = main;\n        ShutdownMode = ShutdownMode.OnMainWindowClose;\n        main.Show();\n    }'''
    new='''    private void OpenMainWindow()\n    {\n        var picker=new InterfacePickerWindow();\n        var mode=picker.ShowDialog()==true ? picker.SelectedMode : "classic";\n        var main = new MainWindow();\n        UiModeService.Apply(main,mode);\n        MainWindow = main;\n        ShutdownMode = ShutdownMode.OnMainWindowClose;\n        main.Show();\n    }'''
    if old in s: s=s.replace(old,new,1)
    # PRO hardened helper
    old2='''    void OpenMain()\n    {\n        var main = new MainWindow();\n        MainWindow = main;\n        ShutdownMode = ShutdownMode.OnMainWindowClose;\n        main.Show();\n        main.Activate();\n    }'''
    new2='''    void OpenMain()\n    {\n        var picker=new InterfacePickerWindow();\n        var mode=picker.ShowDialog()==true ? picker.SelectedMode : "classic";\n        var main = new MainWindow();\n        UiModeService.Apply(main,mode);\n        MainWindow = main;\n        ShutdownMode = ShutdownMode.OnMainWindowClose;\n        main.Show();\n        main.Activate();\n    }'''
    if old2 in s: s=s.replace(old2,new2,1)
p.write_text(s,encoding='utf-8')

# ---- Polished FREE key window (handlers/names unchanged). ----
p=root/'ActivationWindow.xaml'
if p.exists():
    p.write_text(r'''<Window x:Class="RiuClickerCS.ActivationWindow" xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation" xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
 Title="RiuClicker FREE · Key" Width="620" Height="500" WindowStartupLocation="CenterScreen" ResizeMode="NoResize" Background="#060910" Foreground="White">
 <Grid><Border Margin="24" CornerRadius="26" Background="#0D1420" BorderBrush="#26354B" BorderThickness="1"><Grid Margin="30">
  <Grid.RowDefinitions><RowDefinition Height="Auto"/><RowDefinition Height="*"/><RowDefinition Height="Auto"/></Grid.RowDefinitions>
  <StackPanel><TextBlock Text="RIUCLICKER · FREE" Foreground="#22D3EE" FontWeight="Bold" FontSize="12"/><TextBlock Text="GET YOUR KEY" FontSize="34" FontWeight="Black" Margin="0,7,0,5"/><TextBlock Text="Нажми GET KEY → пройди LootLabs → ключ появится автоматически. Ключ действует 24 часа на этом ПК." Foreground="#94A3B8" TextWrapping="Wrap" FontSize="13"/></StackPanel>
  <Border Grid.Row="1" Background="#111A29" BorderBrush="#2C3B52" BorderThickness="1" CornerRadius="20" Padding="22" Margin="0,24,0,18"><StackPanel VerticalAlignment="Center">
   <TextBlock Text="LICENSE KEY" Foreground="#7DD3FC" FontWeight="Bold" FontSize="10"/><TextBox x:Name="KeyBox" Height="50" Margin="0,8,0,14" FontFamily="Consolas" FontSize="17" CharacterCasing="Upper" VerticalContentAlignment="Center"/>
   <Grid><Grid.ColumnDefinitions><ColumnDefinition/><ColumnDefinition/></Grid.ColumnDefinitions><Button x:Name="GetKeyButton" Content="GET KEY · LOOTLABS" Height="48" Margin="0,0,6,0" Click="GetKey_Click" Background="#123047" BorderBrush="#22D3EE" Foreground="White" FontWeight="Bold"/><Button x:Name="ActivateButton" Grid.Column="1" Content="ACTIVATE FREE" Height="48" Margin="6,0,0,0" Click="Activate_Click" Background="#6D28D9" BorderBrush="#A78BFA" Foreground="White" FontWeight="Bold"/></Grid>
   <TextBlock x:Name="StatusText" Text="Press GET KEY to start." Foreground="#94A3B8" Margin="0,14,0,0" TextAlignment="Center" TextWrapping="Wrap"/>
  </StackPanel></Border>
  <Grid Grid.Row="2"><Grid.ColumnDefinitions><ColumnDefinition/><ColumnDefinition/></Grid.ColumnDefinitions><TextBlock Text="FREE · 24H · DEVICE BOUND" Foreground="#64748B"/><TextBlock x:Name="DeviceText" Grid.Column="1" HorizontalAlignment="Right" Foreground="#64748B" FontFamily="Consolas"/></Grid>
 </Grid></Border></Grid>
</Window>''',encoding='utf-8')

# ---- Polished PRO key window (manual paid keys). ----
p=root/'PaidActivationWindow.xaml'
if p.exists():
    p.write_text(r'''<Window x:Class="RiuClickerCS.PaidActivationWindow" xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation" xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
 Title="RiuClicker PRO · Activation" Width="620" Height="480" WindowStartupLocation="CenterScreen" ResizeMode="NoResize" Background="#08050F" Foreground="White">
 <Grid><Border Margin="24" CornerRadius="26" Background="#140C20" BorderBrush="#4C2C68" BorderThickness="1"><Grid Margin="30">
  <Grid.RowDefinitions><RowDefinition Height="Auto"/><RowDefinition Height="*"/><RowDefinition Height="Auto"/></Grid.RowDefinitions>
  <StackPanel><TextBlock Text="RIUCLICKER · PRO" Foreground="#C084FC" FontWeight="Bold" FontSize="12"/><TextBlock Text="PRO ACTIVATION" FontSize="34" FontWeight="Black" Margin="0,7,0,5"/><TextBlock Text="Вставь PRO-ключ. Ключи 30 / 90 дней и Lifetime выдаются отдельно и проверяются сервером." Foreground="#B9A7C9" TextWrapping="Wrap"/></StackPanel>
  <Border Grid.Row="1" Background="#1D112B" BorderBrush="#53366C" BorderThickness="1" CornerRadius="20" Padding="22" Margin="0,24,0,18"><StackPanel VerticalAlignment="Center"><TextBlock Text="PRO LICENSE KEY" Foreground="#D8B4FE" FontWeight="Bold" FontSize="10"/><TextBox x:Name="KeyBox" Height="50" Margin="0,8,0,14" FontFamily="Consolas" FontSize="17" CharacterCasing="Upper" VerticalContentAlignment="Center"/><Button x:Name="ActivateButton" Content="ACTIVATE PRO" Height="50" Click="Activate_Click" Background="#7E22CE" BorderBrush="#C084FC" Foreground="White" FontWeight="Bold"/><TextBlock x:Name="StatusText" Text="30 DAYS · 90 DAYS · LIFETIME" Foreground="#B9A7C9" Margin="0,14,0,0" TextAlignment="Center" TextWrapping="Wrap"/></StackPanel></Border>
  <TextBlock Grid.Row="2" x:Name="DeviceText" Foreground="#806B91" FontFamily="Consolas"/>
 </Grid></Border></Grid>
</Window>''',encoding='utf-8')

# Basic validation.
text='\n'.join(fp.read_text(encoding='utf-8',errors='ignore') for fp in root.glob('*') if fp.suffix in ('.cs','.xaml'))
for m in ['MacroKeyHold','MacroStepGap','MacroRepeatDelay','InterfacePickerWindow','SidebarColumn','MainContentArea']:
    if m not in text: raise SystemExit('missing shared v2 marker: '+m)
print('shared v2 macro + 3-interface + activation UI patch applied')
