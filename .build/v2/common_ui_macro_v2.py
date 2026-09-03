from pathlib import Path
import re, os

root=Path('src')
edition=os.environ.get('RIU_EDITION','FREE').strip().upper()

# Keep the original 5.22 configurable macro editor. It already exposes:
# key/modifier hold, step gap, pointer settle, start delay, repeat count,
# repeat delay, explicit delay steps, key/mouse/coordinate steps and recording.
xaml=root/'MainWindow.xaml'
x=xaml.read_text(encoding='utf-8')
if 'x:Name="PageMacros"' not in x or 'x:Name="MacroKeyHold"' not in x or 'x:Name="MacroStepGap"' not in x:
    raise SystemExit('Original 5.22 macro editor is missing')

# Make the timing controls self-explanatory without changing their handlers.
x=x.replace('Text="Клавиша, мс"','Text="УДЕРЖАНИЕ КЛАВИШИ, МС"')
x=x.replace('Text="SHIFT/CTRL/ALT"','Text="SHIFT / CTRL / ALT, МС"')
x=x.replace('Text="Между шагами"','Text="ПАУЗА МЕЖДУ ШАГАМИ, МС"')
x=x.replace('Text="Перед кликом"','Text="ПЕРЕД КЛИКОМ В ТОЧКУ, МС"')
x=x.replace('Text="Старт, мс"','Text="ЗАДЕРЖКА СТАРТА, МС"')
x=x.replace('Text="Между повторами"','Text="МЕЖДУ ПОВТОРАМИ, МС"')
x=x.replace('Text="ЗАПИСЬ И ДЕЙСТВИЯ"','Text="МАКРОС · ЗАПИСЬ И ШАГИ"')
x=x.replace('Text="Запись 5.22 автоматически сохраняет реальные паузы между нажатиями."',
            'Text="Записывай или собирай вручную. Все цифры задержек сверху можно менять самому."')

# Expose stable names used by the three runtime layouts.
if 'x:Name="SidebarColumn"' not in x:
    x=re.sub(r'<ColumnDefinition Width="(?:232|208)"/><ColumnDefinition Width="\*"/>',
             '<ColumnDefinition x:Name="SidebarColumn" Width="232"/><ColumnDefinition Width="*"/>',x,count=1)
if 'x:Name="MainContentArea"' not in x:
    x=x.replace('<Grid Grid.Column="1" Margin="24,18,24,20">',
                '<Grid x:Name="MainContentArea" Grid.Column="1" Margin="24,18,24,20">',1)
    x=x.replace('<Grid Grid.Column="1" Margin="28,22,28,24">',
                '<Grid x:Name="MainContentArea" Grid.Column="1" Margin="28,22,28,24">',1)

if 'x:Name="SidebarColumn"' not in x or 'x:Name="MainContentArea"' not in x:
    raise SystemExit('Could not name main layout columns')

# Edition badge in the shell.
if edition=='PRO':
    x=x.replace('Text="RIU CONTROL"','Text="RIU PRO CONTROL"')
    x=x.replace('Text="NOVA CONTROL CENTER"','Text="RIU PRO CONTROL"')
else:
    x=x.replace('Text="NOVA CONTROL CENTER"','Text="RIU FREE CONTROL"')
xaml.write_text(x,encoding='utf-8')

# Three actually different interface presets. Every launch shows the picker.
(root/'InterfacePickerWindow.xaml').write_text(r'''<Window x:Class="RiuClickerCS.InterfacePickerWindow"
 xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
 xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
 Title="RiuClicker · Interface" Width="760" Height="470"
 WindowStartupLocation="CenterScreen" ResizeMode="NoResize" Background="#070A10" Foreground="White">
 <Grid Margin="30">
  <Grid.RowDefinitions><RowDefinition Height="Auto"/><RowDefinition Height="*"/><RowDefinition Height="Auto"/></Grid.RowDefinitions>
  <StackPanel>
   <TextBlock Text="RIUCLICKER" Foreground="#22D3EE" FontWeight="Bold" FontSize="12"/>
   <TextBlock Text="ВЫБЕРИ ИНТЕРФЕЙС" FontSize="31" FontWeight="Black" Margin="0,6,0,4"/>
   <TextBlock Text="Выбор появляется при каждом запуске. Функции одинаковые — меняется компоновка и стиль." Foreground="#93A4B8"/>
  </StackPanel>
  <UniformGrid Grid.Row="1" Columns="3" Margin="0,24,0,20">
   <Button Tag="classic" Click="Pick_Click" Margin="6" Padding="16" Background="#101720" BorderBrush="#2D3D50" Foreground="White">
    <StackPanel><TextBlock Text="CLASSIC" FontSize="18" FontWeight="Black"/><TextBlock Text="Баланс" Foreground="#22D3EE" Margin="0,8,0,14"/><Border Height="8" Background="#263848" CornerRadius="4"/><Border Height="8" Background="#1A2531" CornerRadius="4" Margin="0,7,0,0"/><TextBlock Text="Стандартный размер\nи спокойная тёмная тема" TextWrapping="Wrap" Margin="0,18,0,0" Foreground="#9AABBC"/></StackPanel>
   </Button>
   <Button Tag="compact" Click="Pick_Click" Margin="6" Padding="16" Background="#0B1118" BorderBrush="#1E93A8" Foreground="White">
    <StackPanel><TextBlock Text="COMPACT" FontSize="18" FontWeight="Black"/><TextBlock Text="Больше места" Foreground="#4DE4F5" Margin="0,8,0,14"/><UniformGrid Columns="2"><Border Height="34" Background="#14222B" Margin="2" CornerRadius="5"/><Border Height="34" Background="#14222B" Margin="2" CornerRadius="5"/></UniformGrid><TextBlock Text="Узкая панель\nи плотная компоновка" TextWrapping="Wrap" Margin="0,18,0,0" Foreground="#9AABBC"/></StackPanel>
   </Button>
   <Button Tag="neon" Click="Pick_Click" Margin="6" Padding="16" Background="#150C22" BorderBrush="#A855F7" Foreground="White">
    <StackPanel><TextBlock Text="NEON" FontSize="18" FontWeight="Black"/><TextBlock Text="PRO LOOK" Foreground="#D8A8FF" Margin="0,8,0,14"/><Border Height="34" Background="#2A123F" BorderBrush="#A855F7" BorderThickness="1" CornerRadius="9"/><TextBlock Text="Широкий интерфейс\nи фиолетовый неон" TextWrapping="Wrap" Margin="0,18,0,0" Foreground="#B9A6C9"/></StackPanel>
   </Button>
  </UniformGrid>
  <TextBlock Grid.Row="2" Text="Нажми на карточку, чтобы открыть RiuClicker" HorizontalAlignment="Center" Foreground="#65768A"/>
 </Grid>
</Window>''',encoding='utf-8')

(root/'InterfacePickerWindow.xaml.cs').write_text(r'''using System.Windows;
namespace RiuClickerCS;
public partial class InterfacePickerWindow : Window
{
    public string SelectedMode { get; private set; }="classic";
    public InterfacePickerWindow(){InitializeComponent();}
    private void Pick_Click(object sender,RoutedEventArgs e)
    {
        if(sender is FrameworkElement f && f.Tag is string m) SelectedMode=m;
        DialogResult=true; Close();
    }
}
''',encoding='utf-8')

(root/'UiModeService.cs').write_text(r'''using System.Windows;
using System.Windows.Media;
namespace RiuClickerCS;
public static class UiModeService
{
    static void Brush(string key, byte r, byte g, byte b)
    {
        try{if(Application.Current.Resources.Contains(key))Application.Current.Resources[key]=new SolidColorBrush(Color.FromRgb(r,g,b));}catch{}
    }
    public static void Apply(MainWindow w,string mode)
    {
        mode=(mode??"classic").ToLowerInvariant();
        if(mode=="compact")
        {
            w.Width=1080; w.Height=735; w.SidebarColumn.Width=new GridLength(176);
            w.MainContentArea.Margin=new Thickness(15,13,15,15);
            Brush("WindowBrush",5,9,13); Brush("SidebarBrush",6,13,18); Brush("CardBrush",10,20,27);
            Brush("ControlBrush",14,28,36); Brush("AccentBrush",45,212,230); Brush("MutedBrush",125,155,168);
        }
        else if(mode=="neon")
        {
            w.Width=1300; w.Height=850; w.SidebarColumn.Width=new GridLength(252);
            w.MainContentArea.Margin=new Thickness(32,24,32,26);
            Brush("WindowBrush",8,5,14); Brush("SidebarBrush",14,7,23); Brush("CardBrush",24,12,37);
            Brush("ControlBrush",34,17,50); Brush("AccentBrush",168,85,247); Brush("MutedBrush",183,159,202);
        }
        else
        {
            w.Width=1180; w.Height=790; w.SidebarColumn.Width=new GridLength(232);
            w.MainContentArea.Margin=new Thickness(24,18,24,20);
            Brush("WindowBrush",7,10,16); Brush("SidebarBrush",9,13,20); Brush("CardBrush",16,22,32);
            Brush("ControlBrush",22,30,42); Brush("AccentBrush",34,211,238); Brush("MutedBrush",135,149,168);
        }
    }
}
''',encoding='utf-8')

# Show interface picker right before the main window, after licensing.
app=root/'App.xaml.cs'
a=app.read_text(encoding='utf-8')
if 'UiModeService.Apply(main, mode);' not in a:
    # FREE gate method.
    free_old='''    private void OpenMainWindow()\n    {\n        var main = new MainWindow();\n        MainWindow = main;\n        ShutdownMode = ShutdownMode.OnMainWindowClose;\n        main.Show();\n    }'''
    free_new='''    private void OpenMainWindow()\n    {\n        var picker=new InterfacePickerWindow();\n        var mode=picker.ShowDialog()==true?picker.SelectedMode:"classic";\n        var main = new MainWindow();\n        UiModeService.Apply(main, mode);\n        MainWindow = main;\n        ShutdownMode = ShutdownMode.OnMainWindowClose;\n        main.Show();\n    }'''
    if free_old in a:
        a=a.replace(free_old,free_new,1)
    else:
        # PRO hardened startup method.
        pro_old='''    void OpenMain()\n    {\n        var main = new MainWindow();\n        MainWindow = main;\n        ShutdownMode = ShutdownMode.OnMainWindowClose;\n        main.Show();\n        main.Activate();\n    }'''
        pro_new='''    void OpenMain()\n    {\n        var picker=new InterfacePickerWindow();\n        var mode=picker.ShowDialog()==true?picker.SelectedMode:"classic";\n        var main = new MainWindow();\n        UiModeService.Apply(main, mode);\n        MainWindow = main;\n        ShutdownMode = ShutdownMode.OnMainWindowClose;\n        main.Show();\n        main.Activate();\n    }'''
        if pro_old in a: a=a.replace(pro_old,pro_new,1)
        else: raise SystemExit('Main-window open method not found')
app.write_text(a,encoding='utf-8')

# Prettier activation window, keeping all code-behind names/events intact.
if edition=='FREE':
    p=root/'ActivationWindow.xaml'
    if p.exists():
        p.write_text(r'''<Window x:Class="RiuClickerCS.ActivationWindow"
 xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation" xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
 Title="RiuClicker FREE · Key" Width="640" Height="500" WindowStartupLocation="CenterScreen" ResizeMode="NoResize" Background="#070A10" Foreground="White">
 <Grid Margin="32"><Grid.RowDefinitions><RowDefinition Height="Auto"/><RowDefinition Height="*"/><RowDefinition Height="Auto"/></Grid.RowDefinitions>
  <Grid><Grid.ColumnDefinitions><ColumnDefinition/><ColumnDefinition Width="Auto"/></Grid.ColumnDefinitions><StackPanel><TextBlock Text="RIUCLICKER FREE" Foreground="#22D3EE" FontWeight="Black" FontSize="13"/><TextBlock Text="GET YOUR 24H KEY" FontSize="31" FontWeight="Black" Margin="0,7,0,4"/><TextBlock Text="Пройди LootLabs один раз → ключ автоматически появится здесь." Foreground="#94A3B8"/></StackPanel><Border Grid.Column="1" Background="#102730" BorderBrush="#22D3EE" BorderThickness="1" CornerRadius="13" Padding="14,8" VerticalAlignment="Top"><TextBlock Text="FREE · 24H" Foreground="#67E8F9" FontWeight="Bold"/></Border></Grid>
  <Border Grid.Row="1" Margin="0,24,0,18" Background="#0F1621" BorderBrush="#28384A" BorderThickness="1" CornerRadius="22" Padding="24"><StackPanel VerticalAlignment="Center"><TextBlock Text="LICENSE KEY" Foreground="#71849A" FontSize="10" FontWeight="Bold"/><TextBox x:Name="KeyBox" Height="50" Margin="0,8,0,14" FontFamily="Consolas" FontSize="17" CharacterCasing="Upper" VerticalContentAlignment="Center"/><Grid><Grid.ColumnDefinitions><ColumnDefinition/><ColumnDefinition/></Grid.ColumnDefinitions><Button x:Name="GetKeyButton" Content="GET KEY · LOOTLABS" Height="48" Margin="0,0,6,0" Click="GetKey_Click" Background="#132630" BorderBrush="#22D3EE" Foreground="White" FontWeight="Bold"/><Button x:Name="ActivateButton" Grid.Column="1" Content="APPLY KEY" Height="48" Margin="6,0,0,0" Click="Activate_Click" Background="#0891B2" BorderBrush="#22D3EE" Foreground="White" FontWeight="Bold"/></Grid><Border Background="#0A111A" CornerRadius="12" Padding="12" Margin="0,15,0,0"><TextBlock x:Name="StatusText" Text="Нажми GET KEY, пройди LootLabs и дождись ключа." Foreground="#9FB0C3" TextWrapping="Wrap" TextAlignment="Center"/></Border></StackPanel></Border>
  <Grid Grid.Row="2"><Grid.ColumnDefinitions><ColumnDefinition/><ColumnDefinition/></Grid.ColumnDefinitions><TextBlock Text="KEY SYSTEM · ONLINE" Foreground="#526478" FontSize="10"/><TextBlock x:Name="DeviceText" Grid.Column="1" HorizontalAlignment="Right" Foreground="#526478" FontFamily="Consolas" FontSize="10"/></Grid>
 </Grid>
</Window>''',encoding='utf-8')
else:
    p=root/'PaidActivationWindow.xaml'
    if p.exists():
        p.write_text(r'''<Window x:Class="RiuClickerCS.PaidActivationWindow"
 xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation" xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
 Title="RiuClicker PRO · Activation" Width="640" Height="480" WindowStartupLocation="CenterScreen" ResizeMode="NoResize" Background="#090611" Foreground="White">
 <Grid Margin="32"><Grid.RowDefinitions><RowDefinition Height="Auto"/><RowDefinition Height="*"/><RowDefinition Height="Auto"/></Grid.RowDefinitions>
  <Grid><Grid.ColumnDefinitions><ColumnDefinition/><ColumnDefinition Width="Auto"/></Grid.ColumnDefinitions><StackPanel><TextBlock Text="RIUCLICKER" Foreground="#C084FC" FontWeight="Black" FontSize="13"/><TextBlock Text="PRO ACTIVATION" FontSize="31" FontWeight="Black" Margin="0,7,0,4"/><TextBlock Text="PRO-ключ выдаётся владельцем: 30 / 90 дней или Lifetime." Foreground="#A697B6"/></StackPanel><Border Grid.Column="1" Background="#28123C" BorderBrush="#A855F7" BorderThickness="1" CornerRadius="13" Padding="14,8" VerticalAlignment="Top"><TextBlock Text="PRO" Foreground="#E9D5FF" FontWeight="Black"/></Border></Grid>
  <Border Grid.Row="1" Margin="0,24,0,18" Background="#140D20" BorderBrush="#3A2450" BorderThickness="1" CornerRadius="22" Padding="24"><StackPanel VerticalAlignment="Center"><TextBlock Text="PRO LICENSE KEY" Foreground="#806C91" FontSize="10" FontWeight="Bold"/><TextBox x:Name="KeyBox" Height="52" Margin="0,8,0,14" FontFamily="Consolas" FontSize="17" CharacterCasing="Upper" VerticalContentAlignment="Center"/><Button x:Name="ActivateButton" Content="ACTIVATE PRO" Height="50" Click="Activate_Click" Background="#7E22CE" BorderBrush="#A855F7" Foreground="White" FontWeight="Black"/><Border Background="#0D0914" CornerRadius="12" Padding="12" Margin="0,15,0,0"><TextBlock x:Name="StatusText" Text="Вставь PRO-ключ и нажми ACTIVATE PRO." Foreground="#B6A5C5" TextWrapping="Wrap" TextAlignment="Center"/></Border></StackPanel></Border>
  <Grid Grid.Row="2"><Grid.ColumnDefinitions><ColumnDefinition/><ColumnDefinition/></Grid.ColumnDefinitions><TextBlock Text="PRO · SERVER VERIFIED" Foreground="#655471" FontSize="10"/><TextBlock x:Name="DeviceText" Grid.Column="1" HorizontalAlignment="Right" Foreground="#655471" FontFamily="Consolas" FontSize="10"/></Grid>
 </Grid>
</Window>''',encoding='utf-8')

print(f'v2 common UI/macro patch applied for {edition}')
