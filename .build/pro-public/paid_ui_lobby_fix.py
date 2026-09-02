from pathlib import Path
import re

root=Path("src")

# ---- MainWindow.xaml: branding + guaranteed Lobby nav/page ----
p=root/"MainWindow.xaml"
s=p.read_text(encoding="utf-8")

# Fix visible branding regardless of old text.
s=re.sub(r'11\s*[·\-]\s*NOVA CONTROL', '5.22 PRO', s, flags=re.I)
s=re.sub(r'3D\s*[-·]\s*RIU', 'PAID · RIU', s, flags=re.I)

# Add a visible Lobby button after Bolts if absent.
if 'Tag="Lobby"' not in s:
    patterns=[
        r'(<Button[^>]*Content="[^"]*Bolts[^"]*"[^>]*Tag="Bolts"[^>]*/>)',
        r'(<Button[^>]*Tag="Bolts"[^>]*Content="[^"]*Bolts[^"]*"[^>]*/>)',
    ]
    inserted=False
    for pat in patterns:
        ns,n=re.subn(pat, r'\1\n                            <Button Content="◉   Lobby" Tag="Lobby" Style="{StaticResource NavButton}" Click="Nav_Click"/>', s, count=1, flags=re.I)
        if n:
            s=ns; inserted=True; break
    if not inserted:
        # Fallback: put Lobby before Settings nav.
        ns,n=re.subn(r'(<Button[^>]*Tag="Settings"[^>]*/>)',
                     r'<Button Content="◉   Lobby" Tag="Lobby" Style="{StaticResource NavButton}" Click="Nav_Click"/>\n                            \1',
                     s,count=1,flags=re.I)
        if n: s=ns

# Replace or create Lobby page.
lobby=r'''                        <!-- LOBBY PAGE -->
                        <ScrollViewer x:Name="PageLobby" Visibility="Collapsed" VerticalScrollBarVisibility="Auto">
                          <StackPanel>
                            <Border Style="{StaticResource HeroBorder}" Margin="0,0,0,12">
                              <StackPanel>
                                <TextBlock Text="RIU LOBBY" FontSize="24" FontWeight="Black" Foreground="{DynamicResource AccentBrush}"/>
                                <TextBlock Text="Синхронизация физических E / V владельца лобби" Foreground="{DynamicResource MutedBrush}" Margin="0,6,0,0" TextWrapping="Wrap"/>
                                <TextBlock Text="V из Bolt Push внутри программы не отправляется участникам." Foreground="{DynamicResource MutedBrush}" Margin="0,4,0,0" TextWrapping="Wrap"/>
                              </StackPanel>
                            </Border>
                            <Border Style="{StaticResource CardBorder}">
                              <StackPanel>
                                <TextBlock Text="КОД ЛОББИ" Foreground="{DynamicResource MutedBrush}" FontSize="10" FontWeight="Bold"/>
                                <TextBox x:Name="LobbyCodeBox" Height="42" Margin="0,7,0,12" FontFamily="Consolas" FontSize="18" CharacterCasing="Upper"/>
                                <Button Content="СОЗДАТЬ ЛОББИ" Style="{StaticResource AccentButton}" Margin="0,0,0,8" Click="CreateLobby_Click"/>
                                <Button Content="ВОЙТИ В ЛОББИ" Style="{StaticResource RiuButton}" Margin="0,0,0,8" Click="JoinLobby_Click"/>
                                <Button Content="ВЫЙТИ" Style="{StaticResource DangerButton}" Click="LeaveLobby_Click"/>
                                <Border Margin="0,14,0,0" Padding="12" CornerRadius="12" BorderBrush="{DynamicResource BorderBrush}" BorderThickness="1">
                                  <StackPanel>
                                    <TextBlock Text="СТАТУС" Foreground="{DynamicResource MutedBrush}" FontSize="10" FontWeight="Bold"/>
                                    <TextBlock x:Name="LobbyStatusText" Text="OFFLINE" Foreground="{DynamicResource AccentBrush}" FontSize="16" FontWeight="Bold" Margin="0,4,0,0"/>
                                  </StackPanel>
                                </Border>
                              </StackPanel>
                            </Border>
                          </StackPanel>
                        </ScrollViewer>

'''
if 'x:Name="PageLobby"' in s:
    s=re.sub(r'\s*<!-- LOBBY PAGE -->.*?</ScrollViewer>\s*', '\n'+lobby, s, count=1, flags=re.S)
else:
    # Insert before Profiles page / another known page.
    for marker in ['<!-- PROFILES PAGE -->','<!-- SETTINGS PAGE -->','<!-- LOG PAGE -->']:
        if marker in s:
            s=s.replace(marker,lobby+'                        '+marker,1)
            break

p.write_text(s,encoding="utf-8")

# ---- MainWindow.xaml.cs: guarantee nav routing ----
p=root/"MainWindow.xaml.cs"
s=p.read_text(encoding="utf-8")

# Ensure Lobby is hidden/shown alongside pages.
if 'PageLobby.Visibility' not in s:
    vis_lines=list(re.finditer(r'(?m)^\s*Page\w+\.Visibility\s*=\s*page\s*==\s*"[^"]+"\s*\?\s*Visibility\.Visible\s*:\s*Visibility\.Collapsed;\s*$',s))
    if vis_lines:
        m=vis_lines[-1]
        s=s[:m.end()]+'\n        PageLobby.Visibility = page == "Lobby" ? Visibility.Visible : Visibility.Collapsed;'+s[m.end():]

# Ensure title mapping has Lobby.
if '"Lobby"' not in s:
    # Insert into a switch expression if present.
    sw=re.search(r'page\s+switch\s*\{',s)
    if sw:
        pos=sw.end()
        s=s[:pos]+'\n            "Lobby" => ("LOBBY", "E / V sync"),'+s[pos:]

p.write_text(s,encoding="utf-8")

# ---- Force visible paid branding in all source files ----
for bp in root.rglob("*"):
    if bp.suffix.lower() not in (".xaml",".cs"):
        continue
    try:
        bt=bp.read_text(encoding="utf-8")
    except Exception:
        continue
    bt=re.sub(r'11\\s*[·\\-]\\s*NOVA CONTROL', '5.22 PRO', bt, flags=re.I)
    bt=re.sub(r'NOVA CONTROL', '5.22 PRO', bt, flags=re.I)
    bt=re.sub(r'3D\\s*[·\\-]\\s*RIU', 'PAID RIU', bt, flags=re.I)
    bp.write_text(bt,encoding="utf-8")

# ---- Hard validation of the exact UI bits we need ----
checks={
    "Lobby nav": 'Tag="Lobby"',
    "Lobby page": 'x:Name="PageLobby"',
    "Lobby status": 'x:Name="LobbyStatusText"',
}
text=(root/"MainWindow.xaml").read_text(encoding="utf-8")
for name,needle in checks.items():
    if needle not in text:
        raise SystemExit(f"missing {name}: {needle}")

cs=(root/"MainWindow.xaml.cs").read_text(encoding="utf-8")
if 'PageLobby.Visibility' not in cs:
    raise SystemExit("missing Lobby routing")

all_ui="\n".join(
    fp.read_text(encoding="utf-8",errors="ignore")
    for fp in root.rglob("*")
    if fp.suffix.lower() in (".xaml",".cs")
)
if "5.22 PRO" not in all_ui:
    raise SystemExit("missing paid branding anywhere in source")

print("paid UI/lobby fix applied")
