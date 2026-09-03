from pathlib import Path
import re

root=Path("src")

# PRO macro messaging + branding.
p=root/"MainWindow.xaml"
x=p.read_text(encoding="utf-8")
x=x.replace('Одновременно могут работать два разных макроса','PRO · одновременно работают 2 макроса · расширенные задержки и повторы')
x=x.replace('NOVA CONTROL CENTER','RIUCLICKER PRO CONTROL')
x=x.replace('V из Bolt Push внутри программы не отправляется участникам.','Сгенерированные программой нажатия не отправляются участникам.')
if 'PRO ADVANTAGES' not in x:
    needle='<Grid x:Name="PageMacros" Visibility="Collapsed">'
    if needle in x:
        x=x.replace(needle,needle+'\n                            <!-- PRO ADVANTAGES: 2 simultaneous macros + Lobby/Trace -->',1)
p.write_text(x,encoding="utf-8")

# Beautiful paid activation UI.
(root/"PaidActivationWindow.xaml").write_text(r'''<Window x:Class="RiuClickerCS.PaidActivationWindow"
 xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
 xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
 Title="RiuClicker PRO · Activation" Width="660" Height="520"
 WindowStartupLocation="CenterScreen" ResizeMode="NoResize" Foreground="White">
 <Window.Background>
  <LinearGradientBrush StartPoint="0,0" EndPoint="1,1">
   <GradientStop Color="#08050E" Offset="0"/>
   <GradientStop Color="#171021" Offset=".55"/>
   <GradientStop Color="#0A1119" Offset="1"/>
  </LinearGradientBrush>
 </Window.Background>
 <Grid Margin="34">
  <Grid.RowDefinitions><RowDefinition Height="Auto"/><RowDefinition Height="*"/><RowDefinition Height="Auto"/></Grid.RowDefinitions>
  <StackPanel>
   <StackPanel Orientation="Horizontal">
    <Border Background="#24A855F7" BorderBrush="#66A855F7" BorderThickness="1" CornerRadius="10" Padding="10,5">
     <TextBlock Text="RIUCLICKER PRO" Foreground="#E9D5FF" FontSize="11" FontWeight="Bold"/>
    </Border>
    <Border Background="#1822D3EE" BorderBrush="#5522D3EE" BorderThickness="1" CornerRadius="10" Padding="10,5" Margin="8,0,0,0">
     <TextBlock Text="PAID LICENSE" Foreground="#67E8F9" FontSize="11" FontWeight="Bold"/>
    </Border>
   </StackPanel>
   <TextBlock Text="PRO ACTIVATION" FontSize="35" FontWeight="Black" Margin="0,13,0,4"/>
   <TextBlock Text="Введи PRO-ключ. Ключ проверяется сервером и привязывается к этому ПК. PRO включает Lobby / Trace и два одновременно работающих макроса." Foreground="#B7C0D0" FontSize="13.5" TextWrapping="Wrap"/>
  </StackPanel>

  <Border Grid.Row="1" Margin="0,24,0,18" Padding="25" CornerRadius="24" Background="#D9171021" BorderBrush="#594C1D72" BorderThickness="1">
   <StackPanel VerticalAlignment="Center">
    <TextBlock Text="PRO LICENSE KEY" Foreground="#C4B5FD" FontSize="10" FontWeight="Bold"/>
    <Border Background="#080B12" BorderBrush="#4C1D72" BorderThickness="1" CornerRadius="13" Margin="0,7,0,14">
     <TextBox x:Name="KeyBox" Height="52" Padding="14,0" Background="Transparent" BorderThickness="0" Foreground="White" CaretBrush="White" FontFamily="Consolas" FontSize="17" CharacterCasing="Upper" VerticalContentAlignment="Center"/>
    </Border>
    <Button x:Name="ActivateButton" Content="ACTIVATE PRO" Height="52" Click="Activate_Click" Background="#7C3AED" BorderBrush="#C084FC" Foreground="White" FontWeight="Bold" FontSize="13"/>
    <TextBlock x:Name="StatusText" Text="30 DAYS · 90 DAYS · LIFETIME" Foreground="#A5B4C7" TextAlignment="Center" TextWrapping="Wrap" Margin="0,15,0,0"/>
   </StackPanel>
  </Border>

  <Grid Grid.Row="2">
   <Grid.ColumnDefinitions><ColumnDefinition/><ColumnDefinition/></Grid.ColumnDefinitions>
   <StackPanel>
    <TextBlock Text="PRO FEATURES" Foreground="#64748B" FontSize="10" FontWeight="Bold"/>
    <TextBlock Text="2 macros · Lobby · Trace · profiles" Foreground="#A5B4C7" FontSize="11"/>
   </StackPanel>
   <StackPanel Grid.Column="1" HorizontalAlignment="Right">
    <TextBlock Text="DEVICE" Foreground="#64748B" FontSize="10" FontWeight="Bold" HorizontalAlignment="Right"/>
    <TextBlock x:Name="DeviceText" Foreground="#A5B4C7" FontFamily="Consolas" FontSize="10"/>
   </StackPanel>
  </Grid>
 </Grid>
</Window>''',encoding="utf-8")

# Version metadata.
p=root/"RiuClickerCS.csproj"
s=p.read_text(encoding="utf-8")
s=re.sub(r'<Version>[^<]+</Version>','<Version>2.0.0</Version>',s)
s=re.sub(r'<FileVersion>[^<]+</FileVersion>','<FileVersion>2.0.0.0</FileVersion>',s)
s=re.sub(r'<AssemblyVersion>[^<]+</AssemblyVersion>','<AssemblyVersion>2.0.0.0</AssemblyVersion>',s)
p.write_text(s,encoding="utf-8")

for name in ["MainWindow.xaml","MainWindow.xaml.cs","MainWindow.Extras.cs","BrandVisual.cs"]:
    p=root/name
    if p.exists():
        t=p.read_text(encoding="utf-8")
        t=t.replace("RiuClicker 5.22 PRO","RiuClicker PRO 2.0").replace("RIUCLICKER 5.22 PRO","RIUCLICKER PRO 2.0")
        t=t.replace("RiuClicker 5.22","RiuClicker PRO 2.0")
        p.write_text(t,encoding="utf-8")

print("PRO 2.0 polish applied")
