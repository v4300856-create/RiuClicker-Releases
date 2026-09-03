from pathlib import Path
import re

root=Path("src")

# ---------- Keep the original 5.22 configurable macro editor ----------
xaml=root/"MainWindow.xaml"
x=xaml.read_text(encoding="utf-8")
required=[
    'x:Name="PageMacros"',
    'x:Name="MacroKeyHold"',
    'x:Name="MacroModifierHold"',
    'x:Name="MacroStepGap"',
    'x:Name="MacroPointerSettle"',
    'x:Name="MacroStartDelay"',
    'x:Name="MacroRepeatCount"',
    'x:Name="MacroRepeatDelay"',
    'x:Name="MacroDelayBox"',
    'x:Name="MacroStepsList"',
]
for marker in required:
    if marker not in x:
        raise SystemExit("5.22 macro editor marker missing: "+marker)

# Make it explicit that all numeric macro timings are editable.
needle='<TextBlock Text="Запись 5.22 автоматически сохраняет реальные паузы между нажатиями." Foreground="{DynamicResource MutedBrush}" FontSize="10" TextWrapping="Wrap" Margin="0,5,0,0"/>'
if needle in x and 'ВСЕ ЦИФРЫ МОЖНО МЕНЯТЬ' not in x:
    x=x.replace(needle,needle+'<TextBlock Text="ВСЕ ЦИФРЫ МОЖНО МЕНЯТЬ ВРУЧНУЮ · удержание клавиши · задержка между шагами · старт · повторы · паузы" Foreground="{DynamicResource AccentBrush}" FontSize="10" FontWeight="Bold" TextWrapping="Wrap" Margin="0,5,0,0"/>',1)

# Name the shell pieces used by the three runtime interfaces.
x=x.replace('<ColumnDefinition Width="232"/><ColumnDefinition Width="*"/>',
            '<ColumnDefinition x:Name="SidebarColumn" Width="232"/><ColumnDefinition Width="*"/>',1)
x=x.replace('<Grid Grid.Column="1" Margin="24,18,24,20">',
            '<Grid x:Name="MainContentArea" Grid.Column="1" Margin="24,18,24,20">',1)

xaml.write_text(x,encoding="utf-8")

(root/"InterfacePickerWindow.xaml").write_text(r'''<Window x:Class="RiuClickerCS.InterfacePickerWindow"
 xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
 xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
 Title="RiuClicker · Interface" Width="760" Height="470"
 WindowStartupLocation="CenterScreen" ResizeMode="NoResize"
 Background="#070A10" Foreground="#F8FAFC">
 <Grid Margin="28">
  <Grid.RowDefinitions><RowDefinition Height="Auto"/><RowDefinition Height="*"/><RowDefinition Height="Auto"/></Grid.RowDefinitions>
  <StackPanel>
   <TextBlock Text="RIUCLICKER" Foreground="#22D3EE" FontSize="12" FontWeight="Bold"/>
   <TextBlock Text="ВЫБЕРИ ИНТЕРФЕЙС" FontSize="31" FontWeight="Black" Margin="0,7,0,5"/>
   <TextBlock Text="Три разных вида. Выбор появляется при каждом запуске." Foreground="#94A3B8" FontSize="13"/>
  </StackPanel>
  <Grid Grid.Row="1" Margin="0,24,0,18">
   <Grid.ColumnDefinitions><ColumnDefinition/><ColumnDefinition/><ColumnDefinition/></Grid.ColumnDefinitions>
   <Button Grid.Column="0" Tag="classic" Click="Pick_Click" Margin="5" Padding="16" Background="#111827" BorderBrush="#334155" Foreground="White">
    <StackPanel><TextBlock Text="CLASSIC 5.22" FontSize="18" FontWeight="Bold" HorizontalAlignment="Center"/><TextBlock Text="Оригинальная компоновка&#10;бирюзовый акцент&#10;обычная боковая панель" Foreground="#94A3B8" TextAlignment="Center" Margin="0,12,0,0"/></StackPanel>
   </Button>
   <Button Grid.Column="1" Tag="compact" Click="Pick_Click" Margin="5" Padding="16" Background="#0D171A" BorderBrush="#2DD4BF" Foreground="White">
    <StackPanel><TextBlock Text="COMPACT" FontSize="18" FontWeight="Bold" HorizontalAlignment="Center"/><TextBlock Text="Узкая панель&#10;меньше отступов&#10;больше места настройкам" Foreground="#99F6E4" TextAlignment="Center" Margin="0,12,0,0"/></StackPanel>
   </Button>
   <Button Grid.Column="2" Tag="neon" Click="Pick_Click" Margin="5" Padding="16" Background="#171021" BorderBrush="#A855F7" Foreground="White">
    <StackPanel><TextBlock Text="NEON" FontSize="18" FontWeight="Bold" HorizontalAlignment="Center"/><TextBlock Text="Широкий интерфейс&#10;фиолетовый акцент&#10;крупный заголовок" Foreground="#D8B4FE" TextAlignment="Center" Margin="0,12,0,0"/></StackPanel>
   </Button>
  </Grid>
  <TextBlock Grid.Row="2" Text="Выбери один вариант, чтобы открыть RiuClicker" Foreground="#64748B" HorizontalAlignment="Center"/>
 </Grid>
</Window>''',encoding="utf-8")

(root/"InterfacePickerWindow.xaml.cs").write_text(r'''using System.Windows;
namespace RiuClickerCS;
public partial class InterfacePickerWindow : Window
{
    public string SelectedMode { get; private set; } = "classic";
    public InterfacePickerWindow(){InitializeComponent();}
    private void Pick_Click(object sender,RoutedEventArgs e)
    {
        if(sender is FrameworkElement f && f.Tag is string mode) SelectedMode=mode;
        DialogResult=true;
        Close();
    }
}
''',encoding="utf-8")

(root/"UiModeService.cs").write_text(r'''using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;

namespace RiuClickerCS;

public static class UiModeService
{
    static void Brush(string key,string hex)
    {
        if(Application.Current?.Resources is null)return;
        Application.Current.Resources[key]=(Brush)new BrushConverter().ConvertFromString(hex)!;
    }

    public static void Apply(MainWindow w,string? raw)
    {
        var mode=(raw??"classic").ToLowerInvariant();
        if(mode=="compact")
        {
            w.Width=1060; w.Height=720;
            w.SidebarColumn.Width=new GridLength(174);
            w.MainContentArea.Margin=new Thickness(14,12,14,14);
            w.PageTitle.FontSize=25;
            foreach(var b in w.NavPanel.Children.OfType<Button>()){b.FontSize=10.5;b.Padding=new Thickness(10,0,8,0);}
            Brush("AccentBrush","#2DD4BF");
            Brush("AccentSoftBrush","#1D2DD4BF");
            Brush("WindowBrush","#050B0D");
            Brush("SidebarBrush","#071113");
            Brush("CardBrush","#0D171A");
            Brush("ControlBrush","#122126");
        }
        else if(mode=="neon")
        {
            w.Width=1280; w.Height=840;
            w.SidebarColumn.Width=new GridLength(248);
            w.MainContentArea.Margin=new Thickness(32,24,32,26);
            w.PageTitle.FontSize=33;
            foreach(var b in w.NavPanel.Children.OfType<Button>()){b.FontSize=12;b.Padding=new Thickness(16,0,12,0);}
            Brush("AccentBrush","#A855F7");
            Brush("AccentSoftBrush","#24A855F7");
            Brush("WindowBrush","#08050E");
            Brush("SidebarBrush","#0E0818");
            Brush("CardBrush","#171021");
            Brush("ControlBrush","#21172D");
        }
        else
        {
            w.Width=1180; w.Height=790;
            w.SidebarColumn.Width=new GridLength(232);
            w.MainContentArea.Margin=new Thickness(24,18,24,20);
            w.PageTitle.FontSize=29;
            Brush("AccentBrush","#22D3EE");
            Brush("AccentSoftBrush","#2422D3EE");
            Brush("WindowBrush","#070A10");
            Brush("SidebarBrush","#090D14");
            Brush("CardBrush","#101620");
            Brush("ControlBrush","#161E2A");
        }
    }
}
''',encoding="utf-8")

# Inject the interface picker into either FREE OpenMainWindow() or PRO OpenMain().
app=root/"App.xaml.cs"
s=app.read_text(encoding="utf-8")

free_old='''    private void OpenMainWindow()
    {
        var main = new MainWindow();
        MainWindow = main;
        ShutdownMode = ShutdownMode.OnMainWindowClose;
        main.Show();
    }
'''
free_new='''    private void OpenMainWindow()
    {
        var picker = new InterfacePickerWindow();
        var mode = picker.ShowDialog() == true ? picker.SelectedMode : "classic";
        var main = new MainWindow();
        UiModeService.Apply(main, mode);
        MainWindow = main;
        ShutdownMode = ShutdownMode.OnMainWindowClose;
        main.Show();
    }
'''
if free_old in s:
    s=s.replace(free_old,free_new,1)

pro_old='''    void OpenMain()
    {
        var main = new MainWindow();
        MainWindow = main;
        ShutdownMode = ShutdownMode.OnMainWindowClose;
        main.Show();
        main.Activate();
    }
'''
pro_new='''    void OpenMain()
    {
        var picker = new InterfacePickerWindow();
        var mode = picker.ShowDialog() == true ? picker.SelectedMode : "classic";
        var main = new MainWindow();
        UiModeService.Apply(main, mode);
        MainWindow = main;
        ShutdownMode = ShutdownMode.OnMainWindowClose;
        main.Show();
        main.Activate();
    }
'''
if pro_old in s:
    s=s.replace(pro_old,pro_new,1)

# Fallback for the older paid OpenMain without Activate.
pro_old2='''    private void OpenMain()
    {
        var main=new MainWindow();
        MainWindow=main;
        ShutdownMode=ShutdownMode.OnMainWindowClose;
        main.Show();
    }
'''
pro_new2='''    private void OpenMain()
    {
        var picker=new InterfacePickerWindow();
        var mode=picker.ShowDialog()==true?picker.SelectedMode:"classic";
        var main=new MainWindow();
        UiModeService.Apply(main,mode);
        MainWindow=main;
        ShutdownMode=ShutdownMode.OnMainWindowClose;
        main.Show();
    }
'''
if pro_old2 in s:
    s=s.replace(pro_old2,pro_new2,1)

app.write_text(s,encoding="utf-8")

print("v2 common macro + three-interface patch applied")
