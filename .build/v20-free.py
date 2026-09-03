from pathlib import Path
import re

root=Path("src")

# FREE should have one active macro at a time. PRO keeps two.
p=root/"Engines.cs"
s=p.read_text(encoding="utf-8")
s=s.replace('private readonly SemaphoreSlim _slots = new(2, 2);','private readonly SemaphoreSlim _slots = new(1, 1);')
s=s.replace('Уже работают два макроса одновременно','Во FREE одновременно работает один макрос')
p.write_text(s,encoding="utf-8")

p=root/"MainWindow.xaml"
x=p.read_text(encoding="utf-8")
x=x.replace('Одновременно могут работать два разных макроса','FREE · одновременно работает 1 макрос · все задержки настраиваются вручную')
# FREE branding.
x=x.replace('NOVA CONTROL CENTER','RIUCLICKER FREE')
x=x.replace('RiuClicker 5.22','RiuClicker FREE 2.0')
p.write_text(x,encoding="utf-8")

# Prettier FREE LootLabs activation window while preserving all handler names.
(root/"ActivationWindow.xaml").write_text(r'''<Window x:Class="RiuClickerCS.ActivationWindow"
 xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
 xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
 Title="RiuClicker FREE · Key" Width="650" Height="520"
 WindowStartupLocation="CenterScreen" ResizeMode="NoResize" Foreground="White">
 <Window.Background>
  <LinearGradientBrush StartPoint="0,0" EndPoint="1,1">
   <GradientStop Color="#070A10" Offset="0"/>
   <GradientStop Color="#101128" Offset=".55"/>
   <GradientStop Color="#07151A" Offset="1"/>
  </LinearGradientBrush>
 </Window.Background>
 <Grid Margin="34">
  <Grid.RowDefinitions><RowDefinition Height="Auto"/><RowDefinition Height="*"/><RowDefinition Height="Auto"/></Grid.RowDefinitions>
  <StackPanel>
   <Border Background="#1822D3EE" BorderBrush="#5522D3EE" BorderThickness="1" CornerRadius="10" Padding="10,5" HorizontalAlignment="Left">
    <TextBlock Text="FREE · LOOTLABS · 24H" Foreground="#67E8F9" FontSize="11" FontWeight="Bold"/>
   </Border>
   <TextBlock Text="RIUCLICKER FREE" FontSize="34" FontWeight="Black" Margin="0,12,0,4"/>
   <TextBlock Text="Получить ключ можно через LootLabs. Нажми GET KEY, пройди страницу и вставь ключ — либо дождись автоматического получения." Foreground="#A5B4C7" FontSize="13.5" TextWrapping="Wrap"/>
  </StackPanel>

  <Border Grid.Row="1" Margin="0,24,0,18" Padding="24" CornerRadius="24" Background="#D9111720" BorderBrush="#334155" BorderThickness="1">
   <StackPanel VerticalAlignment="Center">
    <TextBlock Text="LICENSE KEY" Foreground="#94A3B8" FontSize="10" FontWeight="Bold"/>
    <Border Background="#080B12" BorderBrush="#334155" BorderThickness="1" CornerRadius="13" Margin="0,7,0,14">
     <TextBox x:Name="KeyBox" Height="50" Padding="14,0" Background="Transparent" BorderThickness="0" Foreground="White" CaretBrush="White" FontFamily="Consolas" FontSize="17" CharacterCasing="Upper" VerticalContentAlignment="Center"/>
    </Border>
    <Grid>
     <Grid.ColumnDefinitions><ColumnDefinition/><ColumnDefinition/></Grid.ColumnDefinitions>
     <Button x:Name="GetKeyButton" Grid.Column="0" Content="GET KEY · LOOTLABS" Height="50" Margin="0,0,6,0" Click="GetKey_Click" Background="#13212A" BorderBrush="#22D3EE" Foreground="#67E8F9" FontWeight="Bold"/>
     <Button x:Name="ActivateButton" Grid.Column="1" Content="APPLY KEY" Height="50" Margin="6,0,0,0" Click="Activate_Click" Background="#7C3AED" BorderBrush="#A78BFA" Foreground="White" FontWeight="Bold"/>
    </Grid>
    <TextBlock x:Name="StatusText" Text="Press GET KEY to start." Foreground="#A5B4C7" TextAlignment="Center" TextWrapping="Wrap" Margin="0,15,0,0"/>
   </StackPanel>
  </Border>

  <Grid Grid.Row="2">
   <Grid.ColumnDefinitions><ColumnDefinition/><ColumnDefinition/></Grid.ColumnDefinitions>
   <StackPanel>
    <TextBlock Text="FREE LICENSE" Foreground="#64748B" FontSize="10" FontWeight="Bold"/>
    <TextBlock Text="24 hours · device bound" Foreground="#94A3B8" FontSize="11"/>
   </StackPanel>
   <StackPanel Grid.Column="1" HorizontalAlignment="Right">
    <TextBlock Text="DEVICE" Foreground="#64748B" FontSize="10" FontWeight="Bold" HorizontalAlignment="Right"/>
    <TextBlock x:Name="DeviceText" Foreground="#94A3B8" FontFamily="Consolas" FontSize="10"/>
   </StackPanel>
  </Grid>
 </Grid>
</Window>''',encoding="utf-8")

# Rebrand version metadata.
p=root/"RiuClickerCS.csproj"
s=p.read_text(encoding="utf-8")
s=re.sub(r'<Version>[^<]+</Version>','<Version>2.0.0</Version>',s)
s=re.sub(r'<FileVersion>[^<]+</FileVersion>','<FileVersion>2.0.0.0</FileVersion>',s)
s=re.sub(r'<AssemblyVersion>[^<]+</AssemblyVersion>','<AssemblyVersion>2.0.0.0</AssemblyVersion>',s)
p.write_text(s,encoding="utf-8")

# Visible version strings.
for name in ["MainWindow.xaml","MainWindow.xaml.cs","MainWindow.Extras.cs","BrandVisual.cs"]:
    p=root/name
    if p.exists():
        t=p.read_text(encoding="utf-8")
        t=t.replace("RiuClicker 5.22","RiuClicker FREE 2.0").replace("RIUCLICKER 5.22","RIUCLICKER FREE 2.0")
        p.write_text(t,encoding="utf-8")

print("FREE 2.0 polish applied")
