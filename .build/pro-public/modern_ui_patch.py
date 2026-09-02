from pathlib import Path
import re

root=Path("src")

# ===== App theme: cleaner 2026 dark/glass look =====
p=root/"App.xaml"
s=p.read_text(encoding="utf-8")
repl={
    '#070A10':'#06080D',
    '#090D14':'#090C12',
    '#101620':'#111720',
    '#161E2A':'#19222E',
    '#0B111A':'#0D131C',
    '#121B28':'#151F2C',
    '#253142':'#2A394B',
    '#182230':'#1C2836',
    '#F3F7FC':'#F6F8FB',
    '#8795A8':'#8C9AAF',
    'CornerRadius="11"':'CornerRadius="13"',
    'CornerRadius="12" Background="{DynamicResource AccentSoftBrush}"':'CornerRadius="14" Background="{DynamicResource AccentSoftBrush}"',
    '<Setter Property="Padding" Value="14,10"/>':'<Setter Property="Padding" Value="15,11"/>',
    '<Setter Property="Height" Value="46"/>':'<Setter Property="Height" Value="43"/>',
    '<Setter Property="Padding" Value="15,0"/>':'<Setter Property="Padding" Value="14,0"/>',
    '<Setter Property="Margin" Value="0,3"/>':'<Setter Property="Margin" Value="0,2"/>',
    '<Setter Property="FontSize" Value="12"/>':'<Setter Property="FontSize" Value="11.5"/>',
    '<Setter Property="CornerRadius" Value="16"/>':'<Setter Property="CornerRadius" Value="20"/>',
    '<Setter Property="Padding" Value="18"/>':'<Setter Property="Padding" Value="20"/>',
    '<Setter Property="Background" Value="#151D28"/>':'<Setter Property="Background" Value="#141B25"/>',
    '<Setter Property="BorderBrush" Value="#34465A"/>':'<Setter Property="BorderBrush" Value="#31445A"/>',
    '<Setter Property="Padding" Value="20"/>':'<Setter Property="Padding" Value="22"/>',
}
for a,b in repl.items():
    s=s.replace(a,b)
p.write_text(s,encoding="utf-8")

# ===== Main shell =====
p=root/"MainWindow.xaml"
x=p.read_text(encoding="utf-8")
x=x.replace('Width="1180" Height="790" MinWidth="1000" MinHeight="660"',
            'Width="1240" Height="820" MinWidth="1040" MinHeight="680"')
x=x.replace('<Grid.RowDefinitions><RowDefinition Height="50"/><RowDefinition Height="*"/></Grid.RowDefinitions>',
            '<Grid.RowDefinitions><RowDefinition Height="56"/><RowDefinition Height="*"/></Grid.RowDefinitions>',1)
x=x.replace('<Grid.ColumnDefinitions><ColumnDefinition Width="232"/><ColumnDefinition Width="*"/></Grid.ColumnDefinitions>',
            '<Grid.ColumnDefinitions><ColumnDefinition Width="208"/><ColumnDefinition Width="*"/></Grid.ColumnDefinitions>',1)
x=x.replace('<Grid Margin="14">','<Grid Margin="12">',1)
x=x.replace('CornerRadius="14" Padding="9" Margin="0,8,0,16"',
            'CornerRadius="18" Padding="8" Margin="0,6,0,13"')
x=x.replace('<Grid Height="58">','<Grid Height="54">',1)
x=x.replace('<Grid.ColumnDefinitions><ColumnDefinition Width="74"/><ColumnDefinition Width="*"/></Grid.ColumnDefinitions>',
            '<Grid.ColumnDefinitions><ColumnDefinition Width="58"/><ColumnDefinition Width="*"/></Grid.ColumnDefinitions>',1)
x=x.replace('x:Name="SidebarBrandViewport" Width="72" Height="56"',
            'x:Name="SidebarBrandViewport" Width="56" Height="50"')
x=x.replace('Grid.Column="1" Margin="6,0,0,0"', 'Grid.Column="1" Margin="4,0,0,0"',1)
x=x.replace('Grid.Column="1" Margin="24,18,24,20"', 'Grid.Column="1" Margin="28,22,28,24"',1)
x=x.replace('x:Name="PageHeaderPanel" Margin="2,0,2,16"', 'x:Name="PageHeaderPanel" Margin="2,0,2,18"',1)
x=x.replace('x:Name="PageTitle" Text="ГЛАВНАЯ" FontSize="29" FontWeight="Black"',
            'x:Name="PageTitle" Text="ГЛАВНАЯ" FontSize="31" FontWeight="Black"')
x=x.replace('FontSize="11.5" Margin="0,2,0,0"', 'FontSize="11" Margin="0,4,0,0"',1)
x=x.replace('CornerRadius="14" BorderBrush="#4F22D3EE" BorderThickness="1" Padding="13,8"',
            'CornerRadius="18" BorderBrush="#4F22D3EE" BorderThickness="1" Padding="14,9"')
x=x.replace('Text="PHYSICAL HOTKEYS" FontSize="9" FontWeight="Bold"',
            'Text="INPUT · READY" FontSize="9" FontWeight="Bold"')
x=x.replace('Text="ОСНОВНОЕ" FontSize="8"', 'Text="CONTROL" FontSize="8"',1)
x=x.replace('Text="ИНСТРУМЕНТЫ" FontSize="8"', 'Text="TOOLS" FontSize="8"',1)
x=x.replace('Text="СИСТЕМА" FontSize="9"', 'Text="STATUS" FontSize="9"',1)
# Cleaner navigation labels while preserving tags/routing.
for a,b in {
    'Content="⌂   Главная"':'Content="⌂   HOME"',
    'Content="⚡   Автокликер"':'Content="⚡   CLICKER"',
    'Content="↗   Wallhop"':'Content="↗   WALLHOP"',
    'Content="◆   Макросы"':'Content="◆   MACROS"',
    'Content="⚙   Настройки"':'Content="⚙   SETTINGS"',
    'Content="◎   Координаты"':'Content="◎   COORDS"',
    'Content="▦   Профили"':'Content="▦   PROFILES"',
    'Content="≡   Журнал"':'Content="≡   LOG"',
    'Content="?   Справка"':'Content="?   HELP"',
}.items():
    x=x.replace(a,b)
# Home hero: remove old NOVA feel visually.
x=x.replace('Text="NOVA CONTROL CENTER"', 'Text="RIU CONTROL"')
x=x.replace('FontSize="20" FontWeight="Black" Foreground="{DynamicResource AccentBrush}"',
            'FontSize="22" FontWeight="Black" Foreground="{DynamicResource AccentBrush}"',1)

x=re.sub(r'\\s+CharacterSpacing="[^"]*"', '', x)
p.write_text(x,encoding="utf-8")

print("modern UI patch applied")
